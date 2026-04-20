"""
Batch job model — tracks PDF invoice classification jobs.

Job state lives in Postgres. The flow is:
  1. User uploads PDF  →  POST /api/v1/batch/upload  →  returns job_id
  2. Frontend connects  →  GET /api/v1/batch/{job_id}/stream  →  SSE events
  3. If connection drops, frontend reconnects and resumes from last event

This means progress survives network hiccups, and we have a history of
every batch job ever run (useful for debugging and analytics).
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from hts_oracle.db import Base


class BatchJob(Base):
    """
    One row per PDF batch classification job.

    Status progression: pending → processing → complete (or → error)
    """
    __tablename__ = "batch_jobs"

    id = Column(Integer, primary_key=True)

    # Original filename (e.g., "invoice_march_2026.pdf")
    filename = Column(String(255))

    # Current status of the job
    #   "pending":    uploaded, not yet started
    #   "processing": actively classifying items
    #   "complete":   all items classified
    #   "error":      something went wrong
    status = Column(String(20), default="pending", nullable=False)

    # Classified items — stored as a JSON array.
    # Each item: { commodity, hts_code, confidence, status, description, duty_rate }
    # Using JSONB instead of a separate table keeps things simple —
    # we always read/write all items together, never query individual items.
    items = Column(JSONB, default=[])

    # Summary stats (set when job completes)
    # { total, classified, needs_review, avg_confidence }
    summary = Column(JSONB, default={})

    # How many items have been processed so far (for progress tracking)
    items_processed = Column(Integer, default=0)
    items_total = Column(Integer, default=0)

    # Current processing phase (for SSE progress events)
    # "extracting_text", "extracting_commodities", "searching", "resolving"
    current_phase = Column(String(50))

    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)