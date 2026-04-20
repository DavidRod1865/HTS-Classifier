"""
Pydantic schemas for the classification API.

These define the exact shape of API requests and responses. Two purposes:
  1. Validation — FastAPI rejects bad requests before hitting our logic
  2. OpenAPI spec — auto-generates docs at /docs, and the frontend can
     generate a typed TypeScript client from it

Why Pydantic over plain dicts?
  If someone sends { "qery": "shirts" } (typo), Pydantic returns a clear
  422 error. With dicts, you'd get a silent None or a confusing KeyError.
"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class ClassifyRequest(BaseModel):
    """
    What the user sends to classify a product.

    The query is required. Refinement fields are optional — they help
    narrow down ambiguous results without needing Claude.

    Example:
        { "query": "cotton t-shirts", "material": "cotton" }
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Product description to classify",
    )

    # Optional refinement fields — collected in the UI's refinement panel.
    # In v1 these were gathered via chat Q&A. In v2 the user fills them upfront.
    material: str | None = Field(None, description="Primary material (e.g., 'cotton', 'steel')")
    intended_use: str | None = Field(None, description="How the product is used (e.g., 'retail')")
    form: str | None = Field(None, description="What the productis made of (e.g., 'knitted', 'woven', 'pipe')")


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class HtsResult(BaseModel):
    """A single HTS code match — rendered as a "result card" in the frontend."""
    hts_code: str
    description: str
    general_rate: str = ""
    special_rate: str = ""
    unit: str = ""
    chapter: str = ""
    context_path: str = ""
    confidence_score: float    # 0-100 scale for display
    similarity: float          # 0-1 scale for logic


class ClassifyResponse(BaseModel):
    """
    Full classification response.

    The 'method' field tells you how results were obtained:
      - "vector_only"  → high confidence, no Claude call (fast + free)
      - "llm_assisted" → Claude helped pick the best match (slower, costs $)
    """
    results: list[HtsResult]
    method: str                  # "vector_only" or "llm_assisted"
    analysis: str | None = None  # Claude's reasoning (only when llm_assisted)
    latency_ms: int