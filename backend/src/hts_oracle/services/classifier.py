"""
Classification orchestrator — the "brain" of the system.

This module decides HOW to classify a product:
  1. Always start with vector search (fast, free)
  2. If confidence is high enough → return results directly
  3. If confidence is low → ask Claude to pick the best match

This is the most important optimization in the system. In practice,
~70% of queries are high-confidence and never touch Claude at all.
That means sub-second responses and near-zero cost for most requests.

The flow:
    User query
        → embed query (OpenAI)
        → vector search (pgvector)
        → confidence check
            ├── HIGH (>= 0.65): return results ← most queries stop here
            └── LOW  (< 0.65):  ask Claude → return results
        → log to audit table
"""

import json
import time

import structlog
from anthropic import AsyncAnthropic
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from hts_oracle.config import get_settings
from hts_oracle.models.classification import Classification
from hts_oracle.services.searcher import search_hts

log = structlog.get_logger()


# ---------------------------------------------------------------------------
# Claude client (cached, like the OpenAI client in embedder.py)
# ---------------------------------------------------------------------------

@lru_cache
def _get_anthropic_client() -> AsyncAnthropic:
    settings = get_settings()
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


# ---------------------------------------------------------------------------
# Claude disambiguation — only called when vector search isn't confident
# ---------------------------------------------------------------------------

async def _ask_claude(query: str, candidates: list[dict], refinements: dict) -> dict:
    """
    Ask Claude to pick the best HTS code from the search candidates.

    Claude receives:
      - The user's product description
      - Any refinement info (material, use, form)
      - The top search results with descriptions

    Claude returns JSON with:
      - "hts_code": the code it thinks is best
      - "analysis": brief explanation of why

    Why Claude and not a cheaper model? Tariff classification requires
    understanding trade law nuances (e.g., "knitted" vs "woven" changes
    the code entirely). Claude handles this well.
    """
    settings = get_settings()
    client = _get_anthropic_client()

    # Build a clear prompt with the candidates
    candidate_text = "\n".join(
        f"  {i+1}. {c['hts_code']} — {c['description']} "
        f"(duty: {c['general_rate']}, confidence: {c['confidence_score']}%)"
        for i, c in enumerate(candidates)
    )

    # Include refinement info if provided
    refinement_text = ""
    if any(refinements.values()):
        parts = [f"  - {k}: {v}" for k, v in refinements.items() if v]
        refinement_text = "\nAdditional product details:\n" + "\n".join(parts)

    prompt = f"""You are an HTS (Harmonized Tariff Schedule) classification expert.

A user wants to classify this product:
  "{query}"
{refinement_text}

Vector search returned these candidates (ranked by similarity):
{candidate_text}

Pick the BEST matching HTS code from the candidates above.

Respond with JSON only (no markdown, no explanation outside the JSON):
{{
  "hts_code": "the best matching code from the candidates",
  "analysis": "1-2 sentences explaining why this is the best match"
}}

If none of the candidates are a good match, pick the closest one and
explain the limitation in your analysis."""

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    # Parse Claude's JSON response.
    # Claude sometimes wraps JSON in markdown code blocks, so we
    # strip those if present.
    response_text = response.content[0].text.strip()
    if response_text.startswith("```"):
        # Remove ```json and ``` wrapping
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If Claude returns invalid JSON, fall back to the top candidate.
        # This is a safety net — it rarely happens in practice.
        log.warn("claude_json_parse_error", response=response_text[:200])
        return {
            "hts_code": candidates[0]["hts_code"] if candidates else "",
            "analysis": "Classification based on vector search (Claude response was unparseable).",
        }


# ---------------------------------------------------------------------------
# Main classification function
# ---------------------------------------------------------------------------

async def classify(
    query: str,
    db: AsyncSession,
    material: str | None = None,
    intended_use: str | None = None,
    form: str | None = None,
) -> dict:
    """
    Classify a product description into an HTS tariff code.

    This is the main entry point called by the API route.

    Args:
        query: Product description (e.g., "cotton t-shirts from China")
        db: Database session
        material/intended_use/form: Optional refinement fields

    Returns:
        {
            "results": [...],      # Ranked HTS code matches
            "method": "...",       # "vector_only" or "llm_assisted"
            "analysis": "...",     # Claude's reasoning (if applicable)
            "latency_ms": 123,     # Total processing time
        }
    """
    settings = get_settings()
    start_time = time.time()

    # --- Build the search text ---
    # If the user provided refinement fields, append them to the query.
    # This gives the embedding more context for better search results.
    # Example: "cotton t-shirts" + material="cotton" + form="knitted"
    #   → "cotton t-shirts material: cotton form: knitted"
    search_text = query
    refinements = {"material": material, "intended_use": intended_use, "form": form}
    refinement_parts = [f"{k}: {v}" for k, v in refinements.items() if v]
    if refinement_parts:
        search_text = f"{query} {' '.join(refinement_parts)}"

    # --- Step 1: Vector search ---
    results = await search_hts(search_text, db)

    if not results:
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "results": [],
            "method": "vector_only",
            "analysis": None,
            "latency_ms": latency_ms,
        }

    # --- Step 2: Confidence gate ---
    # This is THE key optimization. If the top result is confident enough,
    # we skip Claude entirely. No LLM call = fast response + zero cost.
    top_similarity = results[0]["similarity"]
    method = "vector_only"
    analysis = None

    if top_similarity < settings.high_confidence_threshold:
        # Low confidence — ask Claude to help.
        log.info(
            "low_confidence_calling_claude",
            query=query[:100],
            top_similarity=top_similarity,
            threshold=settings.high_confidence_threshold,
        )

        claude_result = await _ask_claude(query, results, refinements)
        method = "llm_assisted"
        analysis = claude_result.get("analysis")

        # If Claude picked a specific code, move it to the top of results.
        picked_code = claude_result.get("hts_code", "")
        if picked_code:
            # Find the picked code in our results and move it to position 0
            for i, r in enumerate(results):
                if r["hts_code"] == picked_code:
                    results.insert(0, results.pop(i))
                    break
    else:
        log.info(
            "high_confidence_skipping_claude",
            query=query[:100],
            top_similarity=top_similarity,
        )

    latency_ms = int((time.time() - start_time) * 1000)

    # --- Step 3: Log to audit table ---
    # Every classification gets recorded for analytics and debugging.
    audit_entry = Classification(
        query_text=query,
        refinements={k: v for k, v in refinements.items() if v},
        top_hts_code=results[0]["hts_code"] if results else None,
        confidence=top_similarity,
        method=method,
        llm_model=settings.claude_model if method == "llm_assisted" else None,
        latency_ms=latency_ms,
    )
    db.add(audit_entry)
    await db.commit()

    return {
        "results": results,
        "method": method,
        "analysis": analysis,
        "latency_ms": latency_ms,
    }