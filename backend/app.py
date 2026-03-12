"""
HTS Oracle — Flask chat API.

Single endpoint: POST /api/chat
    Body:  { "message": "...", "session_id": "..." (optional) }
    Returns: { "session_id": "...", "type": "result"|"question", ... }

Session state (conversation history, clarification count) is kept in memory.
Sessions expire after SESSION_TTL seconds.
"""

import os
import sys
import uuid
import time
import logging
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from hts_search import HTSSearch  # noqa: E402
from pdf_parser import extract_text, extract_commodities  # noqa: E402
from batch_classify import classify_batch, classify_batch_stream, _sse  # noqa: E402
from report_generator import generate_report  # noqa: E402
from csv_updater import update_csv_and_index  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ── CORS ──────────────────────────────────────────────────────────────
FLASK_ENV = os.getenv("FLASK_ENV", "development")
raw_extra_origins = os.getenv("CORS_ORIGINS", "")
extra_origins = [o.strip() for o in raw_extra_origins.split(",") if o.strip()]

if FLASK_ENV == "development":
    CORS(app, origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
    ])
else:
    origins = [o for o in [
        os.getenv("NETLIFY_URL", ""),
        os.getenv("FRONTEND_URL", ""),
    ] if o]
    origins.extend(extra_origins)
    origins.append("https://*.netlify.app")
    CORS(app, origins=origins)

# ── Search engine (initialised once at startup) ──────────────────────
logger.info("Initializing HTS search engine...")
search = HTSSearch()
logger.info("HTS search engine ready")

# ── Session Management ─────────────────────────────────────────────────────
sessions = {}           # session_id  →  { messages, clarification_count, created_at }
SESSION_TTL = 3600      # seconds

def _cleanup_sessions():
    """Drop sessions older than SESSION_TTL."""
    now = time.time()
    expired = [sid for sid, s in sessions.items()
               if now - s.get("created_at", 0) > SESSION_TTL]
    for sid in expired:
        del sessions[sid]


# ── Routes ────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or not (data.get("message") or "").strip():
            return jsonify({"error": "Missing or empty message"}), 400

        message = data["message"].strip()
        session_id = data.get("session_id")

        # Get existing session or create a new one
        if not session_id or session_id not in sessions:
            session_id = str(uuid.uuid4())
            sessions[session_id] = {
                "messages": [],
                "clarification_count": 0,
                "created_at": time.time(),
            }

        # Run classification (mutates session in place)
        result = search.classify(sessions[session_id], message)

        # Periodically sweep expired sessions
        _cleanup_sessions()

        return jsonify({"session_id": session_id, **result})

    except Exception as e:
        logger.error("Chat error: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


# ── File size limits ──────────────────────────────────────────────────
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB (covers CSV uploads)


@app.route("/api/classify-invoice", methods=["POST"])
def classify_invoice():
    """Upload a PDF invoice → extract commodities → classify each → stream progress via SSE."""

    # ── Validate upload before entering the generator ──────────────
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are accepted"}), 400

    pdf_bytes = file.read()
    if len(pdf_bytes) > 10 * 1024 * 1024:
        return jsonify({"error": "PDF file too large (max 10 MB)"}), 400

    filename = file.filename

    def generate():
        try:
            # Phase 1: Extract text
            yield _sse({"event": "phase", "phase": "extracting_text", "progress": 5})
            raw_text = extract_text(pdf_bytes)
            if not raw_text.strip():
                yield _sse({"event": "error", "message": "Could not extract text from PDF"})
                return

            # Phase 2: Extract commodities via Claude
            yield _sse({"event": "phase", "phase": "extracting_commodities", "progress": 15})
            commodities = extract_commodities(raw_text)
            if not commodities:
                yield _sse({"event": "error", "message": "No commodity line items found in invoice"})
                return

            yield _sse({
                "event": "phase",
                "phase": "classifying",
                "progress": 20,
                "total": len(commodities),
            })

            # Phase 3: Classify each commodity (streams item_start / item_done events)
            for chunk in classify_batch_stream(search, commodities):
                yield chunk

        except Exception as e:
            logger.error("Invoice classification error: %s", e, exc_info=True)
            yield _sse({"event": "error", "message": str(e)})

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/generate-report", methods=["POST"])
def generate_report_endpoint():
    """Generate a downloadable PDF report from classified items."""
    try:
        data = request.get_json()
        if not data or not data.get("items"):
            return jsonify({"error": "No items provided"}), 400

        pdf_bytes = generate_report(
            items=data["items"],
            invoice_filename=data.get("filename", ""),
        )

        return send_file(
            __import__("io").BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"hts_classification_report.pdf",
        )

    except Exception as e:
        logger.error("Report generation error: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/update-csv", methods=["POST"])
def update_csv():
    """Upload a new HTS CSV → validate → replace → re-index Pinecone → reload lookup."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if not file.filename or not file.filename.lower().endswith(".csv"):
            return jsonify({"error": "Only CSV files are accepted"}), 400

        csv_bytes = file.read()
        result = update_csv_and_index(csv_bytes, search)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("CSV update error: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "environment": FLASK_ENV})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(debug=(FLASK_ENV == "development"), host="0.0.0.0", port=port)
