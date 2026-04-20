"""
Database connection and session management.

This module creates the async SQLAlchemy engine and provides a session
factory. All database access in the app goes through these.

Key concepts:
  - Engine: the connection pool to Postgres (one per app)
  - Session: a short-lived unit of work (one per request)
  - Base: the declarative base class all ORM models inherit from

The engine is created at startup (init_db) and closed at shutdown (close_db).
Route handlers get a session via the get_db() dependency.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from hts_oracle.config import get_settings


# ---------------------------------------------------------------------------
# Declarative base — all ORM models inherit from this
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    Models that inherit from this get automatic table creation via Alembic
    migrations. Example:

        class HtsCode(Base):
            __tablename__ = "hts_codes"
            id = Column(Integer, primary_key=True)
    """
    pass


# ---------------------------------------------------------------------------
# Engine and session factory (initialized at startup)
# ---------------------------------------------------------------------------
# These start as None and get set in init_db(). This avoids creating
# database connections at import time (which would break tests and
# make the app fragile to import order).

_engine = None
_session_factory = None


async def init_db():
    """
    Create the database engine and session factory.

    Called once at app startup (see main.py lifespan).
    The engine manages a pool of database connections.
    """
    global _engine, _session_factory

    settings = get_settings()

    # Create the async engine with connection pooling.
    # pool_size=5: keep 5 connections open
    # echo=True in dev: logs all SQL queries to the terminal
    _engine = create_async_engine(
        settings.database_url,
        pool_size=5,
        echo=(settings.environment == "development"),
        # statement_cache_size=0: required for Supabase/PgBouncer
        connect_args={"statement_cache_size": 0},
    )

    # Session factory: creates new sessions for each request
    # expire_on_commit=False: objects remain usable after commit
    # (without this, accessing attributes after commit triggers lazy loads)
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def close_db():
    """Close the database engine. Called at app shutdown."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides a database session.

    Usage in a route handler:

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    The session is automatically closed when the request ends.
    """
    async with _session_factory() as session:
        yield session