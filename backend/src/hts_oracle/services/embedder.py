"""
OpenAI embedding service.

Turns text into a 1536-dimensional vector using OpenAI's text-embedding-3-small.

Used by:
  - searcher.py: embed a user's query to search against HTS codes
  - import_hts.py: embed HTS descriptions when building the database

Why a separate module? Both the search service and the import CLI need
to generate embeddings. Keeping this logic in one place avoids duplication
and ensures they use the same model + dimensions.
"""

from functools import lru_cache

from openai import AsyncOpenAI

from hts_oracle.config import get_settings


# Cache the OpenAI client so we reuse the same HTTP connection pool.
# Creating a new client per request wastes time on TCP + TLS handshakes.
@lru_cache
def _get_openai_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def embed_text(text: str) -> list[float]:
    """
    Generate a vector embedding for a single text string.

    Returns a list of 1536 floats (the embedding vector).

    Example:
        vector = await embed_text("cotton t-shirts from China")
        # vector is [0.0123, -0.0456, ...] (1536 numbers)
    """
    settings = get_settings()
    client = _get_openai_client()

    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=text,
        dimensions=settings.embedding_dimensions,
    )

    return response.data[0].embedding


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in one API call.

    Much faster than calling embed_text() in a loop because OpenAI
    processes the entire batch server-side in parallel.

    Example:
        vectors = await embed_batch(["cotton shirts", "steel pipes", "laptop computers"])
        # vectors is [[0.01, ...], [0.02, ...], [0.03, ...]]
    """
    settings = get_settings()
    client = _get_openai_client()

    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
        dimensions=settings.embedding_dimensions,
    )

    return [item.embedding for item in response.data]