"""
Batch classification — run classify_single() for each commodity from an invoice.

Each commodity is classified independently (no shared session state) to avoid
cross-contamination between unrelated line items.
"""

import json
import logging

logger = logging.getLogger(__name__)


def _sse(data):
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


def classify_batch(search, commodities):
    """
    Classify a list of commodity dicts extracted from an invoice.

    Args:
        search: HTSSearch instance
        commodities: list of { description, quantity, unit_price, line_number }

    Returns:
        {
            items: [{ commodity, quantity, unit_price, line_number, classification }],
            summary: { total, classified, needs_review }
        }
    """
    items = []
    classified_count = 0
    review_count = 0

    for commodity in commodities:
        description = commodity.get("description", "")
        if not description:
            continue

        logger.info(f"Classifying: {description[:80]}...")
        classification = search.classify_single(description)

        if classification["type"] == "result":
            classified_count += 1
        else:
            review_count += 1

        items.append({
            "commodity": description,
            "quantity": commodity.get("quantity"),
            "unit_price": commodity.get("unit_price"),
            "line_number": commodity.get("line_number"),
            "classification": classification,
        })

    return {
        "items": items,
        "summary": {
            "total": len(items),
            "classified": classified_count,
            "needs_review": review_count,
        },
    }


def classify_batch_stream(search, commodities):
    """
    Cost-optimised streaming variant.

    Two-phase approach:
        Phase A — Search: embed + Pinecone for each item (streamed per-item).
                  High-confidence items (>= BATCH_CONFIDENCE) are resolved immediately.
        Phase B — Resolve: ONE batched Haiku call for all ambiguous items.

    Yields SSE-formatted strings for the frontend progress bar.
    """
    from hts_search import BATCH_CONFIDENCE

    total = len(commodities)
    search_results = []   # parallel list: { description, results, top_score, commodity }
    confident = []        # indices into search_results that need no Claude
    ambiguous = []        # items to send to the batched Claude call

    # ── Phase A: Search (streams per-item progress) ────────────────
    for i, commodity in enumerate(commodities):
        description = commodity.get("description", "")
        if not description:
            search_results.append(None)
            continue

        yield _sse({
            "event": "item_start",
            "current": i + 1,
            "total": total,
            "commodity": description[:120],
        })

        logger.info(f"Searching: {description[:80]}...")
        sr = search.search_only(description)
        search_results.append({
            "description": description,
            "results": sr["results"],
            "top_score": sr["top_score"],
            "commodity": commodity,
        })

        top_result = None
        if sr["results"]:
            r = sr["results"][0]
            top_result = {
                "hts_code": r.get("hts_code", ""),
                "confidence": r.get("confidence_score", 0),
            }

        if sr["top_score"] >= BATCH_CONFIDENCE and sr["results"]:
            confident.append(i)
            yield _sse({
                "event": "item_done",
                "current": i + 1,
                "total": total,
                "commodity": description[:120],
                "top_result": top_result,
                "status": "confident",
            })
        else:
            ambiguous.append({
                "index": i,
                "description": description,
                "results": sr["results"],
                "top_score": sr["top_score"],
            })
            yield _sse({
                "event": "item_done",
                "current": i + 1,
                "total": total,
                "commodity": description[:120],
                "top_result": top_result,
                "status": "ambiguous",
            })

    # ── Phase B: Resolve ambiguous items in one Haiku call ─────────
    claude_decisions = {}
    if ambiguous:
        yield _sse({
            "event": "phase",
            "phase": "resolving",
            "progress": 85,
            "ambiguous_count": len(ambiguous),
        })
        logger.info(f"Batch-resolving {len(ambiguous)} ambiguous items with Haiku...")
        claude_decisions = search.classify_batch_ambiguous(ambiguous)

    # ── Build final results ────────────────────────────────────────
    items = []
    classified_count = 0
    review_count = 0

    for i, sr in enumerate(search_results):
        if sr is None:
            continue

        if i in confident:
            classification = {
                "type": "result",
                "results": sr["results"][:3],
                "analysis": None,
            }
        elif i in claude_decisions:
            classification = claude_decisions[i]
        else:
            # No results from Pinecone at all
            classification = {
                "type": "needs_review",
                "results": sr["results"][:3],
                "analysis": "Classification is ambiguous — manual review recommended.",
            }

        if classification["type"] == "result":
            classified_count += 1
        else:
            review_count += 1

        items.append({
            "commodity": sr["description"],
            "quantity": sr["commodity"].get("quantity"),
            "unit_price": sr["commodity"].get("unit_price"),
            "line_number": sr["commodity"].get("line_number"),
            "classification": classification,
        })

    yield _sse({
        "event": "complete",
        "items": items,
        "summary": {
            "total": len(items),
            "classified": classified_count,
            "needs_review": review_count,
        },
    })
