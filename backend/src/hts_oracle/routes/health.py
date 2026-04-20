"""
Health check endpoint.

Simple "is the server alive?" check. In production, monitoring tools
(Render, Railway, UptimeRobot) hit this endpoint periodically.
Returns the environment name and a status flag.
"""

from fastapi import APIRouter

from hts_oracle.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Basic health check — confirms the server is running.

    Later we'll add a database connectivity check here so we know
    if both the app AND the database are healthy.
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment,
    }
