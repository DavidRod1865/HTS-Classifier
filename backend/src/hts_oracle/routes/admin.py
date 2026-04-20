"""
Admin API endpoints.

POST /api/v1/admin/import-csv — Upload a new HTS CSV and reimport.

Protected by a simple API key check. Not a full auth system —
just enough to prevent random users from triggering a reimport.
Set ADMIN_API_KEY in your .env to enable.
"""

import csv
import io

import structlog
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Header
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hts_oracle.config import get_settings
from hts_oracle.db import get_db
from hts_oracle.models.hts_code import HtsCode

log = structlog.get_logger()

router = APIRouter(tags=["admin"])


@router.get("/admin/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    Database stats — how many codes, how many have embeddings, etc.
    Useful for the admin dashboard.
    """
    total = await db.scalar(select(func.count(HtsCode.id)))
    with_embeddings = await db.scalar(
        select(func.count(HtsCode.id)).where(HtsCode.embedding.isnot(None))
    )

    return {
        "total_codes": total or 0,
        "with_embeddings": with_embeddings or 0,
        "without_embeddings": (total or 0) - (with_embeddings or 0),
    }
