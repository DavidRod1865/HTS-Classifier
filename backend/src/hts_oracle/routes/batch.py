"""
Batch classification API endpoints.

Two-step flow:
  1. POST /api/v1/batch/upload   → Upload PDF, get a job_id back
  2. GET  /api/v1/batch/{id}/stream → SSE stream of classification progress

Why two steps?
  If the SSE connection drops (network hiccup, browser tab suspended),
  the client can reconnect to the same job_id and resume.
  In v1, all state lived in a Python generator — connection drop = lost progress.
"""

import json
import io
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hts_oracle.db import get_db
from hts_oracle.models.batch_job import BatchJob
from hts_oracle.schemas.batch import BatchUploadResponse
from hts_oracle.services.pdf_parser import extract_text_from_pdf, extract_commodities
from hts_oracle.services.batch_classifier import classify_batch

log = structlog.get_logger()

router = APIRouter(tags=["batch"])

# Max file size: 10MB (matching v1)
MAX_PDF_SIZE = 10 * 1024 * 1024


@router.post("/batch/upload", response_model=BatchUploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a PDF invoice for batch classification.

    Returns a job_id. Use it to connect to the SSE stream at
    GET /api/v1/batch/{job_id}/stream for real-time progress.

    The PDF is processed in the background when you connect to the stream.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Read and validate size
    contents = await file.read()
    if len(contents) > MAX_PDF_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large (max {MAX_PDF_SIZE // 1024 // 1024}MB)")

    # Validate it's actually a PDF (check magic bytes)
    if not contents[:5] == b"%PDF-":
        raise HTTPException(status_code=400, detail="File does not appear to be a valid PDF")

    # Create a batch job record in the database
    job = BatchJob(
        filename=file.filename,
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    log.info("batch_job_created", job_id=job.id, filename=file.filename, size_bytes=len(contents))

    # Store the PDF bytes temporarily in the job's items field
    # (In a production system, you'd store this in S3/GCS instead)
    # For now we'll process it when the stream connects.
    # We store the raw bytes as a base64-encoded string in metadata.
    import base64
    job.items = [{"_pdf_data": base64.b64encode(contents).decode()}]
    await db.commit()

    return BatchUploadResponse(
        job_id=job.id,
        filename=file.filename or "unknown.pdf",
    )


@router.get("/batch/{job_id}/stream")
async def stream_batch_progress(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    SSE stream of batch classification progress.

    Connect to this endpoint after uploading a PDF. Events are streamed
    in real-time as each item is classified.

    Event types:
      - phase: Overall progress update (extracting_text, searching, resolving)
      - item_progress: Individual item status (confident, ambiguous, needs_review)
      - complete: All done — includes full results and summary
      - error: Something went wrong
    """
    # Look up the job
    result = await db.execute(select(BatchJob).where(BatchJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail=f"Batch job {job_id} not found")

    async def event_generator():
        """
        Async generator that processes the PDF and yields SSE events.

        Each event is formatted as: "data: {json}\n\n"
        This is the standard SSE format that browsers' EventSource API understands.
        """
        import base64

        try:
            # Retrieve PDF data from job record
            pdf_data_b64 = ""
            if job.items and len(job.items) > 0 and "_pdf_data" in job.items[0]:
                pdf_data_b64 = job.items[0]["_pdf_data"]

            if not pdf_data_b64:
                yield f"data: {json.dumps({'event': 'error', 'message': 'No PDF data found for this job'})}\n\n"
                return

            pdf_bytes = base64.b64decode(pdf_data_b64)

            # Update job status
            job.status = "processing"
            await db.commit()

            # Phase 1: Extract text from PDF
            yield f"data: {json.dumps({'event': 'phase', 'phase': 'extracting_text', 'progress': 5, 'total': 0})}\n\n"

            pdf_text = await extract_text_from_pdf(io.BytesIO(pdf_bytes))
            if not pdf_text:
                yield f"data: {json.dumps({'event': 'error', 'message': 'Could not extract text from PDF'})}\n\n"
                return

            # Phase 2: Extract commodity line items
            yield f"data: {json.dumps({'event': 'phase', 'phase': 'extracting_commodities', 'progress': 10, 'total': 0})}\n\n"

            commodities = await extract_commodities(pdf_text)

            if not commodities:
                yield f"data: {json.dumps({'event': 'error', 'message': 'No commodity items found in the PDF'})}\n\n"
                return

            job.items_total = len(commodities)
            await db.commit()

            # Phase 3-4: Classify all items (search + resolve)
            # classify_batch is itself an async generator that yields SSE events
            async for event in classify_batch(commodities, db):
                yield f"data: {json.dumps(event)}\n\n"

                # Update job progress in DB
                if event.get("event") == "item_progress":
                    job.items_processed = event.get("index", 0) + 1
                    job.current_phase = event.get("status", "searching")

                elif event.get("event") == "complete":
                    job.status = "complete"
                    job.items = event.get("items", [])
                    job.summary = event.get("summary", {})
                    job.completed_at = datetime.utcnow()

                elif event.get("event") == "error":
                    job.status = "error"

                await db.commit()

        except Exception as e:
            log.error("batch_stream_error", job_id=job_id, error=str(e))
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            job.status = "error"
            await db.commit()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )