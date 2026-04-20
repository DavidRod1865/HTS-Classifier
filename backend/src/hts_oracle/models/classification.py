"""
Classification audit log.

Every single classification query gets logged here.

This table answers questions like:
  - "What are the most common searches?"
  - "How often does Claude get called?" (method = 'llm_assisted')
  - "What's the average confidence score?"
  - "What queries produce low confidence?" (→ improve enriched text for those codes)
  - "How fast are responses?" (latency_ms)
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Float, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from hts_oracle.db import Base


class Classification(Base):
    """
    One row per classification request.

    Tracks what the user asked, what we returned, how confident we were,
    and whether we needed Claude's help.
    """
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True)

    # What the user typed (e.g., "cotton t-shirts from China")
    query_text = Column(Text, nullable=False)

    # Optional refinement fields the user provided
    # Stored as JSON: {"material": "cotton", "intended_use": "retail"}
    refinements = Column(JSONB, default={})

    # The top result we returned
    top_hts_code = Column(String(20))

    # How confident we were (0.0 to 1.0)
    confidence = Column(Float)

    # How was this classified?
    #   "vector_only": high confidence, no Claude needed (fast + free)
    #   "llm_assisted": Claude picked the best match (slower + costs money)
    method = Column(String(20))

    # Which Claude model was used (null if vector_only)
    llm_model = Column(String(50))

    # How long the request took (milliseconds)
    latency_ms = Column(Integer)

    created_at = Column(DateTime, server_default=func.now())