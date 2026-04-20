"""
Pydantic schemas for batch classification.

Defines the SSE (Server-Sent Events) event types that the backend streams
to the frontend during batch PDF processing.

Each event type is a separate model so both backend and frontend have
a clear contract for what data each event carries.
"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# SSE event types — one model per event kind
# ---------------------------------------------------------------------------

class PhaseEvent(BaseModel):
    """Progress update: which phase we're in and overall progress."""
    event: str = "phase"
    phase: str              # "extracting_text", "extracting_commodities", "searching", "resolving"
    progress: int           # 0-100
    total: int = 0          # Total items (set after extraction)

class ItemProgressEvent(BaseModel):
    """One item has been processed (or is starting)."""
    event: str = "item_progress"
    index: int              # Which item (0-based)
    total: int              # Total items
    commodity: str          # Product description
    status: str             # "searching", "confident", "ambiguous"
    hts_code: str = ""      # Best match (empty if still searching)
    confidence: float = 0   # Confidence score 0-100

class CompleteEvent(BaseModel):
    """All items have been classified. Final results."""
    event: str = "complete"
    items: list[dict]       # Full classified items array
    summary: dict           # { total, classified, needs_review, avg_confidence }

class ErrorEvent(BaseModel):
    """Something went wrong during processing."""
    event: str = "error"
    message: str


# ---------------------------------------------------------------------------
# Batch job response (returned by upload endpoint)
# ---------------------------------------------------------------------------

class BatchUploadResponse(BaseModel):
    """Returned when a PDF is uploaded. Use job_id to connect to the SSE stream."""
    job_id: int
    filename: str
    message: str = "Upload successful. Connect to the stream endpoint for progress."