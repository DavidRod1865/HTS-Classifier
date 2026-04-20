"""
Classification API endpoint.

POST /api/v1/classify — takes a product description, returns HTS codes.

This is a thin layer that:
  1. Validates the request (via Pydantic schema)
  2. Calls the classifier service
  3. Returns a typed response

All business logic lives in services/classifier.py, not here.
Route files should be boring — just wiring.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from hts_oracle.db import get_db
from hts_oracle.schemas.classify import ClassifyRequest, ClassifyResponse, HtsResult
from hts_oracle.services.classifier import classify

router = APIRouter(tags=["classification"])


@router.post("/classify", response_model=ClassifyResponse)
async def classify_product(
    request: ClassifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Classify a product description into HTS tariff codes.

    Send a product description and optionally provide material, intended use,
    or form to help narrow down the results.

    **How it works:**
    1. Your description is embedded into a vector (OpenAI)
    2. We search ~8,000 HTS codes for the closest matches (pgvector)
    3. If confidence is high (>= 65%), results are returned directly
    4. If confidence is low, Claude AI helps pick the best match

    **Response:**
    - `results`: Ranked list of matching HTS codes with duty rates
    - `method`: "vector_only" (fast) or "llm_assisted" (Claude helped)
    - `analysis`: Claude's reasoning (only when method is "llm_assisted")
    - `latency_ms`: How long the request took
    """
    result = await classify(
        query=request.query,
        db=db,
        material=request.material,
        intended_use=request.intended_use,
        form=request.form,
    )

    # Convert the raw dicts from classifier into typed Pydantic models.
    # This ensures the response matches our OpenAPI spec exactly.
    return ClassifyResponse(
        results=[HtsResult(**r) for r in result["results"]],
        method=result["method"],
        analysis=result["analysis"],
        latency_ms=result["latency_ms"],
    )