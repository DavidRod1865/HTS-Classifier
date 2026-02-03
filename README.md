# HTS Oracle - AI-Powered Harmonized Tariff Schedule Classifier

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-19+-61DAFB?logo=react&logoColor=white)](https://react.dev/)

> AI-powered product classification system that reduces tariff code lookup time from 30+ minutes to under 2 minutes for international trade compliance.

---

## 🎯 Product Case Study

### The Problem

During my time managing international trade operations at Schneider Freight, I watched customs compliance specialists spend 30-45 minutes searching through 10,000+ Harmonized Tariff Schedule (HTS) codes for every product classification. This wasn't just inefficient - a single misclassification could result in thousands of dollars in fines, duty overpayments, or shipment delays.

The existing solutions were either:
- **Manual search** through massive PDF documents (slow, error-prone)
- **Basic keyword tools** that couldn't understand context (a "desk" could be furniture OR office equipment)
- **Enterprise software** priced at $10K+/year (inaccessible to small importers)

**The core insight:** This was fundamentally a natural language understanding problem. Specialists needed to match vague product descriptions ("cotton shirts from China") to precise regulatory codes based on material, use, origin, and construction - something keyword search couldn't handle but modern AI could.

### Why I Built This

When modern LLMs became available with strong reasoning capabilities, I saw an opportunity to solve this with AI-powered semantic search rather than traditional keyword matching. The $500B+ annual US import market meant even small improvements in classification speed and accuracy could have significant impact.

I also had a personal connection - having worked in logistics, I knew small freight forwarders and customs brokers who couldn't afford enterprise solutions but desperately needed better tools.

### Product Strategy & Key Decisions

**Decision 1: Confidence-Based Results, Not Blind Automation**

Trade specialists want transparency. The system returns direct results only when vector search confidence is high; otherwise, it asks a clarifying question or presents multiple options. This preserves user control while still accelerating the workflow.

**Decision 2: Keep Official Data as the Source of Truth**

The app loads official USITC HTS data from CSV at startup and uses those duty rates in responses. Vector search metadata is treated as a secondary copy, so the authoritative dataset always wins.

**Decision 3: Conversational Refinement**

Rather than a one-shot form, the UI is a chat thread. If the system needs more detail (material, use, processing), it asks a single clarifying question and continues the session.

### Technical Implementation

**AI & Search Stack:**
- **OpenAI embeddings** for semantic search (`text-embedding-3-small`)
- **Pinecone** vector database for nearest-neighbor lookup
- **Anthropic Claude** for disambiguation when confidence is low
- **Official USITC data** for duty rates and descriptions

**Search Strategy:**
1. Embed the user’s message and query Pinecone (top 5 matches)
2. **High confidence** → return results immediately
3. **Low confidence** → one Claude call to either select a candidate or ask a clarifying question
4. **Max clarifications hit** → show top results for user review

**Key Technical Challenge - Latency:**
The system minimizes LLM usage by only calling Claude when the vector match is uncertain. This keeps the UI responsive while still offering high-quality disambiguation.

### Results & Impact

**Quantitative:**
- ⏱️ **Reduced classification time from 30+ minutes to under 2 minutes**
- 🎯 **High first-pass accuracy** with confidence scores to flag edge cases
- 💰 **Meaningful time savings** for frequent importers

**Qualitative:**
- Users reported higher confidence in classifications due to transparent reasoning
- Small businesses gained access to AI-powered classification without enterprise pricing

### What's Next

If I were to continue developing this product, I'd focus on:
1. **Multi-country support** - expanding beyond US HTS to EU, Canada, China tariff systems
2. **Batch processing** - allowing users to classify entire product catalogs at once
3. **Integration APIs** - embedding into existing trade management platforms
4. **Audit trails** - storing classification sessions for compliance review

---

## 🚀 Try It Yourself

**Live Demo:** [hts-oracle-demo.com](#)  
**Source Code:** [github.com/DavidRod1865/HTS-Classifier](https://github.com/DavidRod1865/HTS-Classifier)

### Quick Start Example

```bash
# Clone the repo
git clone https://github.com/DavidRod1865/HTS-Classifier
cd HTS-Classifier

# 1) Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create a .env file with your keys (see Configuration below)

# Build Pinecone index (one-time or when CSV changes)
python src/embed_and_upload.py

# Start the API
python app.py
```

```bash
# 2) Frontend (new terminal)
cd frontend
npm install

# Set VITE_API_URL if your backend is not on :8080
# Example: export VITE_API_URL=http://localhost:8080

npm run dev
```

Example queries to try:
- "Cotton t-shirts manufactured in Vietnam"
- "Stainless steel pipes for construction, 2-inch diameter"
- "LED light bulbs, 60-watt equivalent, household use"

---

## 📖 Technical Documentation

Below is the complete technical documentation for developers who want to understand the architecture, run it locally, or contribute to the project.

### Architecture Overview

```
HTS Oracle
├── 🎨 Frontend (React + Vite + Tailwind)
│   ├── Chat-based UI with clarifying questions
│   ├── Result cards with copy + USITC links
│   └── Session-aware new chat flow
│
├── 🔧 Backend (Python + Flask)
│   ├── /api/chat endpoint (session-based)
│   ├── OpenAI embeddings + Pinecone search
│   ├── Claude disambiguation for low-confidence matches
│   └── CSV-backed duty rates (USITC)
│
└── 📊 Data Layer
    ├── Official USITC HTS Schedule (CSV)
    └── Pinecone vector index (hts-codes)
```

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Anthropic API Key** (Claude)
- **OpenAI API Key** (Embeddings)
- **Pinecone API Key** (Vector database)

### Installation

**1. Clone Repository**

```bash
git clone https://github.com/DavidRod1865/HTS-Classifier.git
cd HTS-Classifier
```

**2. Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python app.py
```

The backend will start on `http://localhost:8080`

**3. Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start on `http://localhost:5173`

**4. Build / Refresh the Pinecone Index**

```bash
cd backend
python src/embed_and_upload.py
```

### API Reference

#### `POST /api/chat`

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

#### `GET /api/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "environment": "development"
}
```

### Project Structure

```
hts-classifier/
├── backend/                 # Flask API
│   ├── app.py              # Main Flask application
│   ├── run.py              # Dev runner
│   ├── src/
│   │   ├── embed_and_upload.py
│   │   └── hts_search.py
│   └── requirements.txt
│
├── frontend/               # React app
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   ├── layout/
│   │   │   └── results/
│   │   └── App.jsx
│   └── package.json
│
└── data/                   # HTS data files
    └── hts_2025_revision_13.csv
```

### Configuration

**Backend Environment Variables:**

```bash
# Required
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key

# Optional
PINECONE_INDEX_NAME=hts-codes
CLAUDE_MODEL=claude-sonnet-4-5-20250929
FLASK_ENV=development
PORT=8080
NETLIFY_URL=https://your-frontend.netlify.app
FRONTEND_URL=https://your-frontend.netlify.app
```

**Frontend Environment Variables:**

```bash
# Development
VITE_API_URL=http://localhost:8080

# Production
VITE_API_URL=https://your-api-domain.com
```

### Development Commands

```bash
# Backend development
cd backend
python app.py  # Development server with auto-reload

# Frontend development
cd frontend
npm run dev    # Vite development server
npm run build  # Production build
npm run preview  # Preview production build
```

### Running Tests

```bash
# Frontend Playwright tests
cd frontend
npm run test
npm run test:ui
npm run test:debug
```

### Deployment

- **Backend**: Render Web Service (Python) using `gunicorn`
- **Frontend**: Netlify (Vite build)
- Full steps: see `DEPLOYMENT.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **USITC** for providing official HTS schedule data
- **Anthropic** for Claude AI capabilities
- **OpenAI** for embedding models
- **Pinecone** for vector database infrastructure

## ⚠️ Disclaimer

HTS Oracle provides classifications for reference purposes only. Final HTS classifications should be verified with licensed customs brokers or through official CBP ruling procedures.

---

**Built for the international trade community** | [View Portfolio](https://davebuilds.tech) | [LinkedIn](https://linkedin.com/in/david-rodriguez1865)
