"""
Initial schema — create all tables + pgvector extension.

This is the first migration. It creates:
  1. The pgvector extension (enables vector column type in Postgres)
  2. hts_codes table (tariff codes with embeddings)
  3. classifications table (audit log)
  4. batch_jobs table (PDF upload job tracking)
  5. HNSW index on the embedding column (for fast similarity search)

Run with: alembic upgrade head
Undo with: alembic downgrade -1

Revision ID: 001
Revises: (none — this is the first migration)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Step 1: Enable pgvector extension ---
    # This must happen BEFORE creating any table with Vector columns.
    # It adds the "vector" data type to Postgres.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- Step 2: hts_codes table ---
    # The main data table. Each row = one HTS tariff code with its
    # duty rates, descriptions, and a vector embedding for search.
    op.create_table(
        "hts_codes",
        sa.Column("id", sa.Integer, primary_key=True),

        # Core identifiers
        sa.Column("hts_number", sa.String(20), unique=True, nullable=False),

        # Three levels of description (raw → enhanced → AI-enriched)
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("enhanced_description", sa.Text),
        sa.Column("enriched_text", sa.Text),

        # Hierarchy
        sa.Column("context_path", sa.Text),
        sa.Column("chapter", sa.String(10)),
        sa.Column("is_leaf", sa.Boolean, default=True),

        # Official duty rates from USITC CSV
        sa.Column("general_rate", sa.String(200)),
        sa.Column("special_rate", sa.Text),
        sa.Column("unit", sa.String(100)),

        # Vector embedding (1536 dims from text-embedding-3-small)
        # Nullable: we might import codes before generating embeddings
        sa.Column("embedding", Vector(1536)),

        # Timestamps
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Index on hts_number for fast lookups
    op.create_index("ix_hts_codes_hts_number", "hts_codes", ["hts_number"])

    # HNSW index on embedding column for fast nearest-neighbor search.
    # vector_cosine_ops: cosine similarity (standard for text embeddings).
    # This is what makes "find the 10 most similar HTS codes" fast.
    op.execute("""
        CREATE INDEX ix_hts_codes_embedding
        ON hts_codes
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # --- Step 3: classifications table (audit log) ---
    op.create_table(
        "classifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("query_text", sa.Text, nullable=False),
        sa.Column("refinements", sa.dialects.postgresql.JSONB, default={}),
        sa.Column("top_hts_code", sa.String(20)),
        sa.Column("confidence", sa.Float),
        sa.Column("method", sa.String(20)),       # "vector_only" or "llm_assisted"
        sa.Column("llm_model", sa.String(50)),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # --- Step 4: batch_jobs table ---
    op.create_table(
        "batch_jobs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("filename", sa.String(255)),
        sa.Column("status", sa.String(20), default="pending", nullable=False),
        sa.Column("items", sa.dialects.postgresql.JSONB, default=[]),
        sa.Column("summary", sa.dialects.postgresql.JSONB, default={}),
        sa.Column("items_processed", sa.Integer, default=0),
        sa.Column("items_total", sa.Integer, default=0),
        sa.Column("current_phase", sa.String(50)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime),
    )


def downgrade() -> None:
    """Reverse everything — drop tables and extension."""
    op.drop_table("batch_jobs")
    op.drop_table("classifications")
    op.drop_index("ix_hts_codes_embedding", table_name="hts_codes")
    op.drop_index("ix_hts_codes_hts_number", table_name="hts_codes")
    op.drop_table("hts_codes")
    op.execute("DROP EXTENSION IF EXISTS vector")