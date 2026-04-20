"""
Shared test fixtures.

These fixtures provide mocked versions of external services (OpenAI, database)
so tests run fast, free, and without network access.

Key fixtures:
  - mock_openai: Patches the OpenAI client to return fake embeddings
  - mock_settings: Overrides app settings for test environment
  - sample_hts_codes: A small set of realistic HTS codes for testing
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from hts_oracle.config import Settings


# ---------------------------------------------------------------------------
# Settings override — use test-safe defaults
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_settings():
    """
    Returns a Settings object with test-safe defaults.

    Overrides API keys with dummy values and points to a test database.
    The lru_cache on get_settings() means we need to patch it.
    """
    return Settings(
        openai_api_key="test-openai-key",
        anthropic_api_key="test-anthropic-key",
        database_url="postgresql+asyncpg://localhost:5432/hts_oracle_test",
        environment="test",
        embedding_model="text-embedding-3-small",
        embedding_dimensions=1536,
    )


# ---------------------------------------------------------------------------
# Mock OpenAI client — returns fake embeddings
# ---------------------------------------------------------------------------

def _fake_embedding(dimensions: int = 1536) -> list[float]:
    """
    Generate a deterministic fake embedding vector.
    """
    return [0.01 * (i % 100) for i in range(dimensions)]
    # This creates a vector like [0.0, 0.01, 0.02, ..., 15.35], which is deterministic and has the right shape.


@pytest.fixture
def mock_openai():
    """
    Patches the OpenAI client so no real API calls are made.

    The mock returns fake embeddings that are the right shape (1536 floats).
    """
    mock_client = AsyncMock()

    # Mock the embeddings.create() response
    mock_embedding = MagicMock()
    mock_embedding.embedding = _fake_embedding()

    mock_response = MagicMock()
    mock_response.data = [mock_embedding]

    mock_client.embeddings.create.return_value = mock_response

    with patch("hts_oracle.services.embedder._get_openai_client", return_value=mock_client):
        yield mock_client


# ---------------------------------------------------------------------------
# Sample HTS codes — realistic test data
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_hts_codes() -> list[dict]:
    """
    A small set of realistic HTS code data for testing.

    These are simplified versions of real codes.
    """
    return [
        {
            "hts_number": "6109.10.0012",
            "description": "T-shirts of cotton, knitted, men's",
            "enhanced_description": "T-shirts of cotton, knitted, men's (Apparel > Knitted > T-shirts)",
            "enriched_text": "Cotton men's t-shirts, knitted or crocheted. Includes crew neck, v-neck, tank tops.",
            "context_path": "Apparel > Knitted > T-shirts",
            "chapter": "61",
            "general_rate": "16.5%",
            "special_rate": "Free (AU,BH,CL,CO)",
            "unit": "Dozen",
        },
        {
            "hts_number": "8471.30.0100",
            "description": "Portable automatic data processing machines",
            "enhanced_description": "Laptop computers (Data processing machines > Portable)",
            "enriched_text": "Laptop and notebook computers, portable data processing machines under 10kg.",
            "context_path": "Data processing machines > Portable",
            "chapter": "84",
            "general_rate": "Free",
            "special_rate": "",
            "unit": "No.",
        },
        {
            "hts_number": "0901.11.0015",
            "description": "Coffee, not roasted, not decaffeinated, Arabica",
            "enhanced_description": "Arabica coffee beans, not roasted (Coffee > Not roasted > Arabica)",
            "enriched_text": "Green arabica coffee beans, unroasted, whole bean, for roasting.",
            "context_path": "Coffee > Not roasted > Arabica",
            "chapter": "09",
            "general_rate": "Free",
            "special_rate": "",
            "unit": "kg",
        },
    ]