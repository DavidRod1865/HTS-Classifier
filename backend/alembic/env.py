"""
Alembic migration environment.

This file tells Alembic how to connect to our database and which models
to track. The key challenge: Alembic runs synchronously, but our app
uses async SQLAlchemy. We bridge this with `run_async()`.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# Import our app's config and models.
# Importing models/__init__.py ensures all model classes are registered
# with Base.metadata — Alembic needs this for --autogenerate to work.
from hts_oracle.config import get_settings
from hts_oracle.db import Base
from hts_oracle.models import HtsCode, Classification, BatchJob  # noqa: F401

# Alembic Config object — provides access to alembic.ini values
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is what Alembic compares against the database to detect changes.
# Base.metadata contains all tables defined by our ORM models.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations without a database connection.

    Generates SQL scripts instead of executing them directly.
    Useful for reviewing what Alembic would do before running it.
    Usage: alembic upgrade head --sql
    """
    settings = get_settings()
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations using an existing database connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Bridge between sync Alembic and our async database.

    Creates an async engine, gets a sync connection from it,
    and runs migrations through that connection.
    """
    settings = get_settings()

    # Create a temporary async engine just for migrations.
    # NullPool: don't keep connections open after migration is done.
    engine = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
        connect_args={"statement_cache_size": 0},
    )

    async with engine.connect() as connection:
        # run_sync bridges async connection → sync Alembic
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


def run_migrations_online() -> None:
    """
    Run migrations with a live database connection.

    This is the normal path when you run `alembic upgrade head`.
    """
    asyncio.run(run_async_migrations())


# Alembic calls one of these based on context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()