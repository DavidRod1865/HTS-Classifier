"""
PDF parsing service — extracts commodity line items from invoice PDFs.

Two-step process:
  1. pdfplumber extracts raw text from the PDF
  2. Claude identifies and extracts the commodity line items

Why Claude for extraction? Invoice formats vary wildly — tables, free text,
multiple columns, different languages. A regex or rule-based parser would
break on every new format. Claude handles the variety reliably.

Why not just Claude for everything? pdfplumber is free and instant.
Claude is expensive and slow. We use pdfplumber for the mechanical part
(PDF → text) and Claude for the intelligent part (text → line items).
"""

import json

import pdfplumber
import structlog
from anthropic import AsyncAnthropic
from functools import lru_cache

from hts_oracle.config import get_settings

log = structlog.get_logger()


@lru_cache
def _get_anthropic_client() -> AsyncAnthropic:
    settings = get_settings()
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


async def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract raw text from a PDF file using pdfplumber.

    pdfplumber handles tables, columns, and rotated text better than
    most PDF libraries. It returns plain text that preserves the
    approximate layout.

    Returns empty string if extraction fails (bad PDF, scanned image, etc.)
    """
    try:
        with pdfplumber.open(pdf_bytes) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            return "\n\n".join(pages_text)
    except Exception as e:
        log.error("pdf_text_extraction_failed", error=str(e))
        return ""


async def extract_commodities(pdf_text: str) -> list[dict]:
    """
    Use Claude to identify commodity line items from invoice text.

    Claude reads the raw text and returns a JSON array of items, each with:
      - "description": what the product is
      - "quantity": how many (if mentioned)
      - "value": dollar amount (if mentioned)

    Example output:
      [
        {"description": "Cotton knitted t-shirts, men's, crew neck", "quantity": "500 pcs", "value": "$2,500"},
        {"description": "Stainless steel hex bolts, M10x40", "quantity": "10,000 pcs", "value": "$850"}
      ]
    """
    if not pdf_text.strip():
        return []

    settings = get_settings()
    client = _get_anthropic_client()

    prompt = f"""You are an expert at reading commercial invoices and packing lists.

Extract ALL commodity line items from this invoice text. For each item, provide:
- "description": A clear, specific product description (include material, form, size if mentioned)
- "quantity": Amount with unit (e.g., "500 pcs", "1000 kg"), or null if not stated
- "value": Dollar amount, or null if not stated

Return ONLY a JSON array. No markdown, no explanation.

Example output:
[
  {{"description": "Cotton knitted t-shirts, men's, crew neck", "quantity": "500 pcs", "value": "$2,500"}},
  {{"description": "Polyester woven fabric, dyed, 150cm width", "quantity": "2000 meters", "value": "$4,200"}}
]

If no commodity items are found, return an empty array: []

Invoice text:
---
{pdf_text[:8000]}
---"""

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = response.content[0].text.strip()

    # Strip markdown code block wrapper if Claude added one
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    try:
        items = json.loads(response_text)
        if not isinstance(items, list):
            log.warn("claude_returned_non_list", response=response_text[:200])
            return []
        log.info("commodities_extracted", count=len(items))
        return items
    except json.JSONDecodeError:
        log.error("commodity_extraction_json_error", response=response_text[:200])
        return []