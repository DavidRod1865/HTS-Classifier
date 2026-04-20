# HTS Oracle

AI-powered Harmonized Tariff Schedule classification. Describe a product, get back the correct HTS code and duty rate — instantly.

## How It Works

1. User submits a product description (or uploads a PDF invoice)
2. The backend embeds the query with OpenAI (`text-embedding-3-small`, 1536 dims)
3. pgvector finds the closest HTS codes by cosine similarity
4. **High confidence** (≥ 0.65) → results returned directly, zero LLM calls
5. **Low confidence** → one Claude Haiku call picks the best match

~70% of queries resolve at step 4 — no LLM needed.

## Features

- **Single product search** — type a description, get ranked HTS codes with duty rates
- **Batch PDF classification** — upload an invoice, results streamed in real-time via SSE
- **Refinement fields** — optional material, intended use, and form inputs to narrow results
- **Admin dashboard** — database stats and import management

## Tech Stack

**Backend** — Python 3.11+
| Component | Technology |
|-----------|------------|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + pgvector (async via SQLAlchemy 2.0 + asyncpg) |
| Migrations | Alembic |
| Embeddings | OpenAI `text-embedding-3-small` |
| LLM | Anthropic Claude Haiku (disambiguation only) |
| PDF parsing | pdfplumber |
| Config | pydantic-settings |
| Logging | structlog |

**Frontend** — Node 20+
| Component | Technology |
|-----------|------------|
| Framework | React 19 + TypeScript 5.6 (strict) |
| Build | Vite 6 |
| Styling | Tailwind CSS 4 |
| Server state | TanStack Query 5 |
| Routing | React Router 7 |
| Icons | lucide-react |

## Project Structure

```
HTS-Classifier/
├── backend/
│   └── src/hts_oracle/
│       ├── main.py            # FastAPI app + middleware
│       ├── config.py          # Environment config
│       ├── db.py              # Async SQLAlchemy + pgvector
│       ├── models/            # HtsCode, Classification, BatchJob
│       ├── services/          # Embedder, Searcher, Classifier, BatchClassifier, PdfParser
│       ├── routes/            # health, classify, batch, admin
│       ├── schemas/           # Pydantic request/response models
│       └── cli/               # CSV import command
├── frontend/src/
│   ├── pages/                 # SearchPage, BatchPage, AdminPage
│   ├── components/            # Search, Results, Batch, Layout
│   ├── api/                   # Typed API client + TanStack Query hooks
│   └── lib/                   # Utilities
└── data/                      # Official USITC HTS CSV files
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node 20+
- PostgreSQL with [pgvector](https://github.com/pgvector/pgvector) extension

### Database Setup

```bash
createdb hts_oracle
psql hts_oracle -c "CREATE EXTENSION IF NOT EXISTS vector"
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Configure environment
cp .env.example .env.local
# Edit .env.local with your API keys and DATABASE_URL

# Run migrations
alembic upgrade head

# Import HTS data
python -m hts_oracle.cli.import_hts ../data/hts_2026_revision_4_enriched.csv

# Start dev server
uvicorn hts_oracle.main:app --reload --port 8080
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # Starts on :5173, proxies /api → :8080
```

## Environment Variables

### Backend (`.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `OPENAI_API_KEY` | Yes | OpenAI API key for embeddings |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude disambiguation |
| `HIGH_CONFIDENCE_THRESHOLD` | No | Similarity threshold for skipping LLM (default: `0.65`) |
| `BATCH_CONFIDENCE_THRESHOLD` | No | Threshold for batch mode (default: `0.55`) |
| `ENVIRONMENT` | No | `development` or `production` |

### Frontend

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Production only | Backend URL (dev uses Vite proxy) |

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/classify` | Classify a single product description |
| POST | `/api/v1/batch/upload` | Upload a PDF for batch classification |
| GET | `/api/v1/batch/{id}/stream` | SSE stream of batch progress |
| GET | `/api/v1/admin/stats` | Database statistics |

## Deployment

**Backend** — Render or Railway

The included `Procfile` runs Uvicorn with a 120s keep-alive timeout (required for SSE streaming).

**Frontend** — Netlify

The included `netlify.toml` configures SPA routing, asset caching, and security headers. Run `npm run build` to produce the `dist/` output.
