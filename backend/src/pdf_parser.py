"""
PDF invoice parsing — extract text, then use Claude to identify commodity line items.

Two-step process:
    1. pdfplumber extracts raw text from each page
    2. Claude parses that text into structured commodity descriptions
"""

import os
import io
import json
import re
import logging
import pdfplumber
from anthropic import Anthropic

logger = logging.getLogger(__name__)

CLAUDE_MODEL_LIGHT = os.getenv("CLAUDE_MODEL_LIGHT", "claude-haiku-4-5-20251001")


def extract_text(pdf_bytes):
    """Extract all text from a PDF, page by page, concatenated."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def extract_commodities(raw_text):
    """
    Use Claude to parse invoice text into structured commodity line items.

    Returns a list of dicts:
        [{ description: str, quantity: str|None, unit_price: str|None, line_number: int }]
    """
    if not raw_text.strip():
        return []

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = (
        "You are an invoice parser. Extract every distinct product or commodity "
        "line item from the invoice text below.\n\n"
        "For each item, extract:\n"
        "- description: A clear commodity description suitable for tariff classification "
        "(include material, form, and intended use when mentioned)\n"
        "- quantity: The quantity ordered (null if not stated)\n"
        "- unit_price: The unit price (null if not stated)\n"
        "- line_number: Sequential number starting from 1\n\n"
        "Rules:\n"
        "- Focus ONLY on physical goods/commodities. Ignore shipping charges, taxes, "
        "discounts, addresses, dates, invoice numbers, and totals.\n"
        "- If a product has a vague name (e.g. 'Item A'), still include it with "
        "whatever description is available.\n"
        "- Combine relevant details (material, color, size) into the description.\n"
        "- Return ONLY a JSON array, no other text.\n\n"
        f"Invoice text:\n{raw_text}\n\n"
        "Respond with ONLY a valid JSON array:"
    )

    response = client.messages.create(
        model=CLAUDE_MODEL_LIGHT,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    return _parse_commodities_response(response.content[0].text)


def _parse_commodities_response(text):
    """Parse Claude's JSON array of commodities, with fallback."""
    try:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        items = json.loads(match.group() if match else text)
        if not isinstance(items, list):
            return []
        # Ensure each item has at minimum a description
        return [
            {
                "description": item.get("description", "").strip(),
                "quantity": item.get("quantity"),
                "unit_price": item.get("unit_price"),
                "line_number": item.get("line_number", i + 1),
            }
            for i, item in enumerate(items)
            if item.get("description", "").strip()
        ]
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Failed to parse commodity extraction response")
        return []
