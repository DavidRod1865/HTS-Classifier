"""
Tests for the search service.

These tests verify that search_hts():
  1. Embeds the query text
  2. Queries pgvector for nearest neighbors
  3. Formats results correctly with duty rates and confidence scores
  4. Handles empty results gracefully

Since we can't easily spin up a real pgvector database in unit tests,
these tests mock the database layer. Integration tests with a real
database would go in a separate test_integration/ directory.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from hts_oracle.services.searcher import search_hts, _format_result
from hts_oracle.models.hts_code import HtsCode


# ---------------------------------------------------------------------------
# Tests for _format_result (pure function, no mocking needed)
# ---------------------------------------------------------------------------

class TestFormatResult:
    """Tests for the result formatting function."""

    def test_formats_basic_result(self):
        """Should include all expected fields with correct values."""
        code = HtsCode(
            hts_number="6109.10.0012",
            description="T-shirts of cotton",
            enhanced_description="T-shirts of cotton (Apparel > Knitted > T-shirts)",
            context_path="Apparel > Knitted > T-shirts",
            chapter="61",
            general_rate="16.5%",
            special_rate="Free (AU,BH,CL)",
            unit="Dozen",
        )

        result = _format_result(code, similarity=0.87)

        assert result["hts_code"] == "6109.10.0012"
        assert result["description"] == "T-shirts of cotton (Apparel > Knitted > T-shirts)"
        assert result["general_rate"] == "16.5%"
        assert result["special_rate"] == "Free (AU,BH,CL)"
        assert result["unit"] == "Dozen"
        assert result["chapter"] == "61"
        assert result["confidence_score"] == 87.0      # 0-100 scale
        assert result["similarity"] == 0.87             # 0-1 scale

    def test_uses_enhanced_description_over_raw(self):
        """Should prefer enhanced_description when available."""
        code = HtsCode(
            hts_number="0101.21.0010",
            description="Males",  # Raw description (terse)
            enhanced_description="Males (Live horses > Purebred breeding animals)",
        )
        result = _format_result(code, similarity=0.5)

        # Should use the more descriptive version
        assert "Live horses" in result["description"]
        assert result["description"] != "Males"

    def test_falls_back_to_raw_description(self):
        """When enhanced_description is empty, use raw description."""
        code = HtsCode(
            hts_number="0101.21.0010",
            description="Males",
            enhanced_description=None,
        )
        result = _format_result(code, similarity=0.5)

        assert result["description"] == "Males"

    def test_handles_missing_optional_fields(self):
        """None values should become empty strings, not 'None'."""
        code = HtsCode(
            hts_number="0101.21.0010",
            description="Males",
            general_rate=None,
            special_rate=None,
            unit=None,
            chapter=None,
            context_path=None,
        )
        result = _format_result(code, similarity=0.5)

        assert result["general_rate"] == ""
        assert result["special_rate"] == ""
        assert result["unit"] == ""
        assert result["chapter"] == ""
        assert result["context_path"] == ""

    def test_confidence_score_rounds_correctly(self):
        """Confidence should round to 1 decimal place."""
        code = HtsCode(hts_number="test", description="test")
        result = _format_result(code, similarity=0.8765)

        assert result["confidence_score"] == 87.7  # Rounded to 1 decimal
        assert result["similarity"] == 0.8765


# ---------------------------------------------------------------------------
# Tests for search_hts (requires mocking DB and embedder)
# ---------------------------------------------------------------------------

class TestSearchHts:
    """Tests for the main search function."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session that returns pre-defined results."""
        session = AsyncMock()
        return session

    @pytest.fixture(autouse=True)
    def patch_deps(self, mock_settings):
        """Patch settings and embedder for all search tests."""
        with (
            patch("hts_oracle.services.searcher.get_settings", return_value=mock_settings),
            patch("hts_oracle.services.searcher.embed_text") as mock_embed,
        ):
            # Return a fake embedding vector
            mock_embed.return_value = [0.01] * 1536
            self.mock_embed = mock_embed
            yield

    async def test_returns_empty_list_when_no_results(self, mock_db):
        """Should gracefully handle an empty database."""
        # Mock DB returns no rows
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        results = await search_hts("nonexistent product", mock_db)

        assert results == []

    async def test_embeds_query_text(self, mock_db):
        """Should call the embedder with the user's query."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        await search_hts("cotton t-shirts from China", mock_db)

        self.mock_embed.assert_called_once_with("cotton t-shirts from China")

    async def test_formats_database_rows_into_results(self, mock_db):
        """Should convert raw DB rows into formatted result dicts."""
        # Mock a database row (what pgvector returns)
        mock_row = MagicMock()
        mock_row.hts_number = "6109.10.0012"
        mock_row.description = "T-shirts of cotton"
        mock_row.enhanced_description = "T-shirts of cotton (Apparel > Knitted)"
        mock_row.context_path = "Apparel > Knitted"
        mock_row.chapter = "61"
        mock_row.general_rate = "16.5%"
        mock_row.special_rate = "Free (AU)"
        mock_row.unit = "Dozen"
        mock_row.distance = 0.13  # Cosine distance (similarity = 1 - 0.13 = 0.87)

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute.return_value = mock_result

        results = await search_hts("cotton shirts", mock_db)

        assert len(results) == 1
        assert results[0]["hts_code"] == "6109.10.0012"
        assert results[0]["general_rate"] == "16.5%"
        assert results[0]["similarity"] == pytest.approx(0.87, abs=0.01)

    async def test_respects_top_k_parameter(self, mock_db):
        """Should return at most top_k results."""
        # Return 5 mock rows
        mock_rows = []
        for i in range(5):
            row = MagicMock()
            row.hts_number = f"code_{i}"
            row.description = f"description_{i}"
            row.enhanced_description = None
            row.context_path = None
            row.chapter = None
            row.general_rate = None
            row.special_rate = None
            row.unit = None
            row.distance = 0.1 + (i * 0.05)
            mock_rows.append(row)

        mock_result = MagicMock()
        mock_result.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_result

        # Request only 3
        results = await search_hts("test query", mock_db, top_k=3)

        assert len(results) == 3

    async def test_results_ordered_by_similarity(self, mock_db):
        """Results should be ordered highest similarity first."""
        mock_rows = []
        for distance in [0.3, 0.1, 0.5]:  # Unordered distances
            row = MagicMock()
            row.hts_number = f"code_{distance}"
            row.description = "test"
            row.enhanced_description = None
            row.context_path = None
            row.chapter = None
            row.general_rate = None
            row.special_rate = None
            row.unit = None
            row.distance = distance
            mock_rows.append(row)

        mock_result = MagicMock()
        # DB returns them sorted by distance (lowest = most similar)
        mock_result.fetchall.return_value = sorted(mock_rows, key=lambda r: r.distance)
        mock_db.execute.return_value = mock_result

        results = await search_hts("test", mock_db, top_k=10)

        # First result should have highest similarity (lowest distance)
        assert results[0]["similarity"] > results[1]["similarity"]
        assert results[1]["similarity"] > results[2]["similarity"]