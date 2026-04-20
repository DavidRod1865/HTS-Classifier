"""
Tests for the embedding service.

These tests verify that:
  1. embed_text() calls OpenAI with the right model and dimensions
  2. embed_batch() handles multiple texts in one call
  3. The returned vectors have the expected shape

All tests use the mock_openai fixture — no real API calls.
"""

import pytest
from unittest.mock import MagicMock, patch

from hts_oracle.services.embedder import embed_text, embed_batch


# We need to patch get_settings because the embedder reads config at call time
@pytest.fixture(autouse=True)
def patch_settings(mock_settings):
    with patch("hts_oracle.services.embedder.get_settings", return_value=mock_settings):
        yield


class TestEmbedText:
    """Tests for single-text embedding."""

    async def test_returns_vector_of_correct_length(self, mock_openai):
        """The embedding should be a list of 1536 floats."""
        result = await embed_text("cotton t-shirts")

        assert isinstance(result, list)
        assert len(result) == 1536
        assert all(isinstance(x, float) for x in result)

    async def test_calls_openai_with_correct_model(self, mock_openai):
        """Should use text-embedding-3-small with 1536 dimensions."""
        await embed_text("cotton t-shirts")

        mock_openai.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input="cotton t-shirts",
            dimensions=1536,
        )

    async def test_passes_user_text_to_openai(self, mock_openai):
        """The exact user text should be sent to OpenAI, unmodified."""
        await embed_text("steel pipes for industrial use")

        call_args = mock_openai.embeddings.create.call_args
        assert call_args.kwargs["input"] == "steel pipes for industrial use"


class TestEmbedBatch:
    """Tests for batch embedding (multiple texts in one API call)."""

    async def test_returns_list_of_vectors(self, mock_openai):
        """Should return one vector per input text."""
        # Set up mock to return 3 embeddings
        mock_embeddings = []
        for i in range(3):
            mock_item = MagicMock()
            mock_item.embedding = [0.01 * j for j in range(1536)]
            mock_embeddings.append(mock_item)

        mock_response = MagicMock()
        mock_response.data = mock_embeddings
        mock_openai.embeddings.create.return_value = mock_response

        result = await embed_batch(["text 1", "text 2", "text 3"])

        assert len(result) == 3
        assert all(len(v) == 1536 for v in result)

    async def test_sends_all_texts_in_one_call(self, mock_openai):
        """Batch embedding should make exactly ONE API call, not N calls."""
        # Mock for 2 embeddings
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.0] * 1536) for _ in range(2)]
        mock_openai.embeddings.create.return_value = mock_response

        await embed_batch(["text 1", "text 2"])

        # Should be called exactly once (not twice)
        assert mock_openai.embeddings.create.call_count == 1

        # The input should be the full list of texts
        call_args = mock_openai.embeddings.create.call_args
        assert call_args.kwargs["input"] == ["text 1", "text 2"]