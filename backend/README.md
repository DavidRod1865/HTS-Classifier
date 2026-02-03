# HTS Oracle Backend API

Flask-based API for HTS (Harmonized Tariff Schedule) classification with a chat-style workflow. It combines OpenAI embeddings + Pinecone vector search and uses Anthropic Claude only when disambiguation is needed.

## 🏗️ Architecture

```
User Message → OpenAI Embedding → Pinecone Search
  ├─ High confidence → return results
  ├─ Low confidence  → Claude picks best result or asks a clarifying question
  └─ Clarification limit → return top results
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API Key (embeddings)
- Pinecone API Key
- Anthropic API Key (Claude)

### Installation

```bash
# From project root
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file in `backend/`:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
ANTHROPIC_API_KEY=your_claude_api_key

# Optional
PINECONE_INDEX_NAME=hts-codes
CLAUDE_MODEL=claude-sonnet-4-5-20250929
FLASK_ENV=development
PORT=8080
NETLIFY_URL=https://your-frontend.netlify.app
FRONTEND_URL=https://your-frontend.netlify.app
```

### Build the Pinecone Index (one-time per CSV update)

```bash
cd backend
python src/embed_and_upload.py
```

### Run the Server

```bash
python app.py
```

API starts at `http://localhost:8080`.

## 📡 API Endpoints

### `POST /api/chat`

Chat-based classification endpoint.

**Request:**
```json
{
  "message": "cotton t-shirts from China",
  "session_id": "optional-session-id"
}
```

**Response (classification):**
```json
{
  "session_id": "2e3a8f8e-...",
  "type": "result",
  "results": [
    {
      "hts_code": "6109.10.0000",
      "description": "T-shirts, singlets and other vests, knitted or crocheted, of cotton",
      "effective_duty": "16.5%",
      "special_duty": "Free (AU,BH,CL,CO,D,E,IL,JO,KR,MA,OM,P,PA,PE,S,SG)",
      "unit": "Dozen",
      "confidence_score": 95,
      "chapter": "61",
      "match_type": "vector_search",
      "duty_source": "usitc"
    }
  ],
  "analysis": "Brief explanation or null"
}
```

**Response (clarifying question):**
```json
{
  "session_id": "2e3a8f8e-...",
  "type": "question",
  "question": "Are these t-shirts knitted or woven?"
}
```

### `GET /api/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "environment": "development"
}
```

## 🧠 Core Logic

The main classification logic lives in `src/hts_search.py`.

- Builds an embedding from the conversation’s user messages
- Queries Pinecone for the top 5 matches
- Returns results immediately for high confidence
- Otherwise uses a single Claude call to choose or ask a clarifying question

CSV duty data is loaded at startup from `data/hts_2025_revision_13.csv` and is treated as the source of truth.

## 📦 Dependencies

- `flask`, `flask-cors`
- `openai` (embeddings)
- `pinecone` (vector search)
- `anthropic` (Claude)
- `pandas` (CSV parsing)

## 🔒 Security Notes

- Do not commit API keys
- Restrict production CORS via `NETLIFY_URL` / `FRONTEND_URL`

---

For frontend integration, see [Frontend README](../frontend/README.md).
