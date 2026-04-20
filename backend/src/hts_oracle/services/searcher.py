"""
Vector search service — finds HTS codes similar to a user's query.

This is the CORE of the whole system. The classification pipeline,
batch processing, and API endpoints all call into this service.

How it works:
  1. User types "cotton t-shirts"
  2. We embed that text → 1536-dim vector
  3. pgvector finds the closest HTS code vectors using cosine similarity
  4. We return the top matches with similarity scores and duty rates

pgvector's <=> operator computes cosine DISTANCE (0 = identical, 2 = opposite).
We convert to similarity (1 - distance) so higher = better match.
"""

import structlog
from sqlalchemy import select, text, bindparam
from sqlalchemy.ext.asyncio import AsyncSession

from hts_oracle.config import get_settings
from hts_oracle.models.hts_code import HtsCode
from hts_oracle.services.embedder import embed_text

log = structlog.get_logger()


# ---------------------------------------------------------------------------
# Result type — what we return from a search
# ---------------------------------------------------------------------------
# Using a plain dict here for simplicity. In a larger app you might use
# a Pydantic model, but dicts are easier to serialize and pass around.

def _format_result(code: HtsCode, similarity: float) -> dict:
    """
    Format an HtsCode row + similarity score into the result shape
    that the API returns to the frontend.

    This is the single place that defines what a "result" looks like.
    If you need to add a field (e.g., "tariff_notes"), add it here.
    """
    return {
        "hts_code": code.hts_number,
        "description": code.enhanced_description or code.description,
        "general_rate": code.general_rate or "",
        "special_rate": code.special_rate or "",
        "unit": code.unit or "",
        "chapter": code.chapter or "",
        "context_path": code.context_path or "",
        "confidence_score": round(similarity * 100, 1),  # 0-100 scale for display
        "similarity": round(similarity, 4),               # 0-1 scale for logic
    }


# ---------------------------------------------------------------------------
# Main search function
# ---------------------------------------------------------------------------

async def search_hts(
    query: str,
    db: AsyncSession,
    top_k: int | None = None,
) -> list[dict]:
    """
    Search for HTS codes matching a text query.

    Args:
        query: The user's product description (e.g., "cotton t-shirts")
        db: Database session (injected by FastAPI dependency)
        top_k: How many results to return (default: from settings)

    Returns:
        List of result dicts sorted by similarity (highest first).
        Each dict has: hts_code, description, general_rate, confidence_score, etc.

    Example:
        results = await search_hts("cotton t-shirts from China", db)
        # results[0]["hts_code"] = "6109.10.0012"
        # results[0]["confidence_score"] = 87.3
    """
    settings = get_settings()
    if top_k is None:
        top_k = settings.search_top_k

    # Step 1: Embed the user's query
    log.info("embedding_query", query=query[:100])
    query_vector = await embed_text(query)

    # Step 2: Find the closest vectors in the database.
    #
    # The SQL uses pgvector's <=> operator (cosine distance).
    # We fetch more candidates than needed (search_candidates) and then
    # take the top_k. This over-fetching improves result quality because
    # HNSW is an approximate index — fetching more gives it a better
    # chance of finding the true nearest neighbors.
    #
    # The HNSW index (created in our migration) makes this fast:
    # ~1-5ms for 8K rows, even with 1536 dimensions.

    fetch_count = settings.search_candidates  # Default: 30

    # Raw SQL for the pgvector cosine distance operator (<=>).
    # We use $1 and $2 positional params because asyncpg doesn't support
    # named :params, and the :: cast syntax conflicts with SQLAlchemy's
    # :name parameter syntax.
    vector_str = str(query_vector)

    stmt = text(
        "SELECT id, hts_number, description, enhanced_description, enriched_text, "
        "context_path, chapter, is_leaf, general_rate, special_rate, unit, "
        "(embedding <=> cast(:qvec as vector)) AS distance "
        "FROM hts_codes "
        "WHERE embedding IS NOT NULL AND is_leaf = true "
        "ORDER BY embedding <=> cast(:qvec as vector) "
        "LIMIT :lim"
    )

    result = await db.execute(
        stmt,
        {"qvec": vector_str, "lim": fetch_count},
    )
    rows = result.fetchall()

    if not rows:
        log.warn("no_search_results", query=query[:100])
        return []

    # Step 3: Convert distance → similarity and format results.
    # Cosine distance range is [0, 2]. Similarity = 1 - distance.
    # So: distance 0 = similarity 1.0 (identical), distance 1 = similarity 0.0.
    results = []
    for row in rows[:top_k]:
        similarity = 1.0 - row.distance

        # Build an HtsCode-like object from the raw row for formatting
        code = HtsCode(
            hts_number=row.hts_number,
            description=row.description,
            enhanced_description=row.enhanced_description,
            context_path=row.context_path,
            chapter=row.chapter,
            general_rate=row.general_rate,
            special_rate=row.special_rate,
            unit=row.unit,
        )
        results.append(_format_result(code, similarity))

    log.info(
        "search_complete",
        query=query[:100],
        num_results=len(results),
        top_score=results[0]["similarity"] if results else 0,
    )

    return results