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
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from hts_search import HTSSearch  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ── CORS ──────────────────────────────────────────────────────────────
FLASK_ENV = os.getenv("FLASK_ENV", "development")

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
    origins.append("https://*.netlify.app")
    CORS(app, origins=origins)

# ── Search engine (initialised once at startup) ──────────────────────
logger.info("Initializing HTS search engine...")
search = HTSSearch()
logger.info("HTS search engine ready")

# ── Session store ─────────────────────────────────────────────────────
# In-memory.  Fine for a single Heroku dyno.  Swap for Redis if you scale.
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


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "environment": FLASK_ENV})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(debug=(FLASK_ENV == "development"), host="0.0.0.0", port=port)
