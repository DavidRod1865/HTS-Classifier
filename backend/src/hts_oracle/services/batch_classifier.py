"""
Batch classification service — classifies all items from a PDF invoice.

This implements the two-phase optimization from v1:

  Phase A — Search (per-item, streamed):
    For each commodity, embed and search pgvector.
    High-confidence items (>= 0.55) are resolved immediately.
    Low-confidence items are collected for Phase B.

  Phase B — Resolve (one batched Claude call):
    All ambiguous items are sent to Claude in a single prompt.
    Claude analyzes them together and returns the best match for each.
    This is MUCH cheaper than one Claude call per item.

Why 0.55 for batch (not 0.65 like interactive)?
  Batch mode is less sensitive to individual accuracy because users
  review results in a table. A slightly wrong classification can be
  caught and corrected. The lower threshold means fewer Claude calls.
"""

import json
from typing import AsyncGenerator

import structlog
from anthropic import AsyncAnthropic
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from hts_oracle.config import get_settings
from hts_oracle.services.searcher import search_hts

log = structlog.get_logger()


@lru_cache
def _get_anthropic_client() -> AsyncAnthropic:
    settings = get_settings()
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


async def classify_batch(
    commodities: list[dict],
    db: AsyncSession,
) -> AsyncGenerator[dict, None]:
    """
    Classify a list of commodity items, yielding SSE events as progress is made.

    This is an async generator — it yields dict events that the route handler
    converts to SSE format and streams to the frontend.

    Args:
        commodities: List of items from pdf_parser.extract_commodities()
                     Each has: description, quantity (optional), value (optional)
        db: Database session for pgvector search

    Yields:
        SSE event dicts: phase, item_progress, complete, error
    """
    settings = get_settings()
    total = len(commodities)

    if total == 0:
        yield {"event": "error", "message": "No items found in the PDF"}
        return

    # --- Phase A: Search each item ---
    yield {"event": "phase", "phase": "searching", "progress": 20, "total": total}

    classified_items = []
    ambiguous_items = []  # Items that need Claude's help

    for i, commodity in enumerate(commodities):
        description = commodity.get("description", "")
        if not description:
            continue

        # Update progress
        progress = 20 + int(65 * i / total)  # 20% to 85%
        yield {
            "event": "item_progress",
            "index": i,
            "total": total,
            "commodity": description[:80],
            "status": "searching",
        }

        # Search pgvector for this item
        results = await search_hts(description, db, top_k=5)

        if not results:
            # No results at all — mark as needs review
            item = {
                "commodity": description,
                "quantity": commodity.get("quantity"),
                "value": commodity.get("value"),
                "hts_code": "",
                "description": "",
                "confidence": 0,
                "general_rate": "",
                "status": "needs_review",
            }
            classified_items.append(item)
            yield {
                "event": "item_progress",
                "index": i,
                "total": total,
                "commodity": description[:80],
                "status": "needs_review",
                "hts_code": "",
                "confidence": 0,
            }
            continue

        top_result = results[0]
        top_similarity = top_result["similarity"]

        if top_similarity >= settings.batch_confidence_threshold:
            # High confidence — resolve immediately, no Claude needed
            item = {
                "commodity": description,
                "quantity": commodity.get("quantity"),
                "value": commodity.get("value"),
                "hts_code": top_result["hts_code"],
                "description": top_result["description"],
                "confidence": top_result["confidence_score"],
                "general_rate": top_result["general_rate"],
                "status": "confident",
            }
            classified_items.append(item)
            yield {
                "event": "item_progress",
                "index": i,
                "total": total,
                "commodity": description[:80],
                "status": "confident",
                "hts_code": top_result["hts_code"],
                "confidence": top_result["confidence_score"],
            }
        else:
            # Low confidence — collect for Phase B
            ambiguous_items.append({
                "index": len(classified_items),  # Position in final list
                "commodity": commodity,
                "candidates": results[:5],
            })
            # Add placeholder to maintain ordering
            classified_items.append({
                "commodity": description,
                "quantity": commodity.get("quantity"),
                "value": commodity.get("value"),
                "hts_code": "",
                "description": "",
                "confidence": 0,
                "general_rate": "",
                "status": "ambiguous",
            })
            yield {
                "event": "item_progress",
                "index": i,
                "total": total,
                "commodity": description[:80],
                "status": "ambiguous",
            }

    # --- Phase B: Resolve ambiguous items with one Claude call ---
    if ambiguous_items:
        yield {"event": "phase", "phase": "resolving", "progress": 85, "total": total}

        resolved = await _resolve_ambiguous_batch(ambiguous_items)

        # Update the classified_items with Claude's decisions
        for resolution in resolved:
            idx = resolution["index"]
            if 0 <= idx < len(classified_items):
                classified_items[idx].update({
                    "hts_code": resolution.get("hts_code", ""),
                    "description": resolution.get("description", ""),
                    "confidence": resolution.get("confidence", 0),
                    "general_rate": resolution.get("general_rate", ""),
                    "status": "llm_assisted",
                })

    # --- Summary ---
    confident_count = sum(1 for item in classified_items if item["status"] in ("confident", "llm_assisted"))
    needs_review = sum(1 for item in classified_items if item["status"] in ("ambiguous", "needs_review"))
    avg_confidence = (
        sum(item["confidence"] for item in classified_items if item["confidence"] > 0)
        / max(confident_count, 1)
    )

    summary = {
        "total": len(classified_items),
        "classified": confident_count,
        "needs_review": needs_review,
        "avg_confidence": round(avg_confidence, 1),
    }

    yield {
        "event": "complete",
        "items": classified_items,
        "summary": summary,
    }


async def _resolve_ambiguous_batch(ambiguous_items: list[dict]) -> list[dict]:
    """
    Send all ambiguous items to Claude in ONE call.

    This is the key cost optimization: instead of N Claude calls (one per item),
    we send all ambiguous items together. Claude analyzes them in context and
    returns a decision for each.
    """
    settings = get_settings()
    client = _get_anthropic_client()

    # Build the prompt with all ambiguous items
    items_text = ""
    for i, item in enumerate(ambiguous_items):
        commodity = item["commodity"]["description"]
        candidates = "\n".join(
            f"    - {c['hts_code']}: {c['description']} (confidence: {c['confidence_score']}%)"
            for c in item["candidates"]
        )
        items_text += f"\nItem {i+1}: \"{commodity}\"\n  Candidates:\n{candidates}\n"

    prompt = f"""You are an HTS classification expert. For each item below, pick the BEST
matching HTS code from its candidates.

{items_text}

Respond with a JSON array. Each element must have:
  - "item_index": which item (1-based)
  - "hts_code": the best code from the candidates
  - "analysis": 1 sentence explaining why

Example: [{{"item_index": 1, "hts_code": "6109.10.0012", "analysis": "Cotton knitted t-shirt matches this heading."}}]

Respond with JSON only, no markdown."""

    try:
        response = await client.messages.create(
            model=settings.claude_model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        decisions = json.loads(response_text)

        # Map Claude's decisions back to our items
        resolved = []
        for decision in decisions:
            item_idx = decision.get("item_index", 0) - 1  # Convert 1-based to 0-based
            if 0 <= item_idx < len(ambiguous_items):
                picked_code = decision.get("hts_code", "")
                # Find the matching candidate to get full details
                candidates = ambiguous_items[item_idx]["candidates"]
                match = next((c for c in candidates if c["hts_code"] == picked_code), None)

                resolved.append({
                    "index": ambiguous_items[item_idx]["index"],
                    "hts_code": picked_code,
                    "description": match["description"] if match else "",
                    "confidence": match["confidence_score"] if match else 50,
                    "general_rate": match["general_rate"] if match else "",
                })

        return resolved

    except Exception as e:
        log.error("batch_claude_resolution_failed", error=str(e))
        # Fallback: use the top candidate for each ambiguous item
        return [
            {
                "index": item["index"],
                "hts_code": item["candidates"][0]["hts_code"] if item["candidates"] else "",
                "description": item["candidates"][0]["description"] if item["candidates"] else "",
                "confidence": item["candidates"][0]["confidence_score"] if item["candidates"] else 0,
                "general_rate": item["candidates"][0]["general_rate"] if item["candidates"] else "",
            }
            for item in ambiguous_items
        ]