"""
FastAPI application factory.

This is the entry point for the entire backend. It creates the FastAPI app,
wires up middleware (CORS, logging), and connects to the database on startup.

Run in development:
    uvicorn hts_oracle.main:app --reload --port 8080

Run in production:
    uvicorn hts_oracle.main:app --host 0.0.0.0 --port $PORT
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hts_oracle.config import get_settings
from hts_oracle.db import init_db, close_db
from hts_oracle.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from hts_oracle.routes import health, classify, batch, admin

# ---------------------------------------------------------------------------
# Structured logging setup
# ---------------------------------------------------------------------------
# structlog outputs JSON in production (machine-readable for log aggregators)
# and pretty-printed text in development (human-readable in terminal).

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,        # Attach request_id etc.
        structlog.processors.add_log_level,             # Add "level": "info"
        structlog.processors.TimeStamper(fmt="iso"),    # Add ISO timestamp
        structlog.dev.ConsoleRenderer()                 # Pretty terminal output
        if get_settings().environment == "development"
        else structlog.processors.JSONRenderer(),       # JSON for production
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()


# ---------------------------------------------------------------------------
# App lifespan — runs on startup and shutdown
# ---------------------------------------------------------------------------
# With lifespan events, we explicitly control when the database connects
# and disconnects. If the DB is unreachable, the app fails at startup — not
# when the first user request comes in.

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    log.info("starting_up", environment=settings.environment, port=settings.port)

    # Connect to database
    await init_db()
    log.info("database_connected")

    yield  # App is running and serving requests

    # Shutdown: close database connections
    await close_db()
    log.info("shutdown_complete")


# ---------------------------------------------------------------------------
# Create the FastAPI application
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """
    Application factory pattern.

    Why a factory? So tests can create a fresh app instance with different
    settings (e.g., a test database URL) without import side-effects.
    """
    settings = get_settings()

    app = FastAPI(
        title="HTS Oracle",
        description="AI-powered HTS tariff code classification",
        version="2.0.0",
        lifespan=lifespan,
    )

    # --- CORS middleware ---
    # Allows the React frontend (running on a different port/domain)
    # to call our API. Without this, browsers block cross-origin requests.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Security + rate limiting middleware ---
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)

    # --- Register route modules ---
    # Each module in routes/ handles a group of related endpoints.
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(classify.router, prefix="/api/v1")
    app.include_router(batch.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")

    return app


# The app instance that uvicorn imports.
# uvicorn hts_oracle.main:app
app = create_app()