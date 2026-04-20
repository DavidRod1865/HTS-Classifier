"""
HTS Code model — the core data table.

Each row is one leaf-level HTS tariff code (e.g., 6109.10.0000 = cotton t-shirts). Both duty rates and embeddings live in the same row. One source of truth.

The `embedding` column stores a 1536-dimensional vector (from OpenAI's
text-embedding-3-small). pgvector's HNSW index makes nearest-neighbor
searches fast (~1-5ms for ~8K rows).
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, Index
from sqlalchemy.sql import func

from hts_oracle.db import Base


class HtsCode(Base):
    """
    A single HTS (Harmonized Tariff Schedule) code.

    Example row:
        hts_number:   "6109.10.0000"
        description:  "T-shirts, singlets, tank tops and similar garments, knitted"
        general_rate: "16.5%"
        chapter:      "61"
    """
    __tablename__ = "hts_codes"

    id = Column(Integer, primary_key=True)

    # --- Core identifiers ---
    # hts_number: The official code like "6109.10.0000"
    # We index this for fast lookups when Claude returns a code
    hts_number = Column(String(20), unique=True, nullable=False, index=True)

    # --- Descriptions (three levels of detail) ---
    # description: The raw USITC text (often terse, e.g., "Of cotton")
    # enhanced_description: Full context path added (e.g., "Of cotton (T-shirts > Knitted > Of cotton)")
    # enriched_text: AI-generated detailed text for better semantic search
    description = Column(Text, nullable=False)
    enhanced_description = Column(Text)
    enriched_text = Column(Text)

    # --- Hierarchy ---
    # context_path: Breadcrumb trail (e.g., "Apparel > Knitted > T-shirts")
    # chapter: First 2 digits of HTS code (e.g., "61")
    # is_leaf: Only leaf nodes are searchable (non-leaves are category headers)
    context_path = Column(Text)
    chapter = Column(String(10))
    is_leaf = Column(Boolean, default=True)

    # --- Duty rates (from official USITC CSV) ---
    # general_rate: Standard rate (e.g., "16.5%", "Free", "2.4¢/kg")
    # special_rate: Preferential rates by trade agreement (e.g., "Free (AU,BH,CL)")
    # unit: Unit of quantity (e.g., "Dozen", "kg", "No.")
    general_rate = Column(String(200))
    special_rate = Column(Text)
    unit = Column(String(100))

    # --- Vector embedding ---
    # 1536-dimensional vector from OpenAI text-embedding-3-small.
    # This is what pgvector searches against when a user types a query.
    # Nullable because we might import codes before generating embeddings.
    embedding = Column(Vector(1536))

    # --- Timestamps ---
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # --- Indexes ---
    # HNSW index on the embedding column for fast nearest-neighbor search.
    # vector_cosine_ops: use cosine similarity (good for text embeddings).
    # m=16, ef_construction=64: HNSW tuning params (defaults work well for <100K vectors).
    __table_args__ = (
        Index(
            "ix_hts_codes_embedding",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def __repr__(self):
        return f"<HtsCode {self.hts_number}: {self.description[:50]}>"