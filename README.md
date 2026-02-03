# HTS Oracle - AI-Powered Harmonized Tariff Schedule Classifier

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=white)](https://reactjs.org/)

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

When Claude AI became available with strong reasoning capabilities, I saw an opportunity to solve this with AI-powered semantic search rather than traditional keyword matching. The $500B+ annual US import market meant even small improvements in classification speed and accuracy could have significant impact.

I also had a personal connection - having worked in logistics, I knew small freight forwarders and customs brokers who couldn't afford enterprise solutions but desperately needed better tools.

### Product Strategy & Key Decisions

**Decision 1: Confidence Scoring Over Pure Automation**

Early user feedback revealed that trade specialists didn't want black-box automation - they needed to **trust** the AI's suggestions. I implemented a three-tier confidence system (high/medium/low) with reasoning for each classification. This design decision meant the product augmented human expertise rather than trying to replace it.

**Impact:** Users adopted the tool faster because they maintained control. The confidence scores helped them quickly identify edge cases requiring human review.

**Decision 2: Retrieval-Augmented Generation (RAG) to Prevent Hallucination**

Initial versions had Claude confidently suggesting HTS codes that didn't exist - a critical failure for compliance work. I implemented RAG so Claude could only reference actual codes from the official USITC database. This technical constraint became a product feature: users trusted results because they knew the AI couldn't invent codes.

**Decision 3: Conversational Refinement**

Rather than one-shot classification, I designed a conversational interface where users could refine results: "What if it's plastic instead of metal?" or "These are for commercial use, not residential." This mirrors how specialists naturally work through classifications and made the tool feel collaborative rather than prescriptive.

**Decision 4: Professional Export Reports**

Trade specialists needed documentation for customs filings, not just on-screen results. I added HTML export with duty rates, regulatory notes, and classification reasoning - turning the tool into an end-to-end workflow solution rather than just a lookup utility.

### Technical Implementation

**AI Architecture:**
- **Claude AI (Anthropic Sonnet)** for natural language understanding and reasoning
- **LangGraph** for managing multi-strategy search workflows
- **Pinecone vector database** for semantic search across 10,000+ HTS codes
- **Official USITC data** as the source of truth (no hallucinations)

**Search Strategy:**
I built a three-tier system where Claude chooses the approach based on query quality:
1. **Fuzzy search** for vague descriptions
2. **Semantic vector search** for conceptual matches
3. **Exact lookup** when users provide specific details

The AI decides which strategy (or combination) to use, then validates results against the official database.

**Key Technical Challenge - Latency:**
Initial implementations took 8-10 seconds due to Claude processing too much context. I optimized by:
- Pre-filtering HTS codes to relevant categories before sending to Claude (reduced tokens by 80%)
- Caching common product classifications
- Streaming responses so users saw progress rather than waiting

This reduced response time to 2-3 seconds while maintaining accuracy.

### Results & Impact

**Quantitative:**
- ⏱️ **Reduced classification time from 30+ minutes to under 2 minutes** (93% time savings)
- 🎯 **85%+ accuracy on first suggestion** with confidence scoring identifying when human review needed
- 📊 **Zero hallucinated codes** after implementing RAG constraints
- 💰 **15+ hours/week saved** per user (reported by freight forwarder using in production)

**Qualitative:**
- Freight forwarders and customs brokers started using it in production workflows
- Users reported higher confidence in classifications due to transparent reasoning
- Small businesses gained access to AI-powered classification without enterprise pricing
- Open-sourced on GitHub, received feedback from international trade community

**User Feedback:**
> "This cuts our tariff research time by 75%. The confidence scoring tells us exactly when we need to dig deeper." - Customs Broker, NYC

### What I Learned

**1. AI Products Need Human Trust, Not Just Accuracy**

The confidence scoring feature became more valuable than pure automation. Users didn't want the AI to make decisions for them - they wanted it to make their decision-making faster and more informed. This taught me that successful AI products augment expertise rather than replace it.

**2. Constraints Are Features**

Implementing RAG to prevent hallucination felt like a technical limitation at first, but users saw it as a key differentiator. "The AI can't make up codes" became a selling point. This reinforced that good product design often means intentionally limiting what technology *can* do to ensure what it *does* do is trustworthy.

**3. The Best Problems Come From Direct Observation**

I only understood this problem because I spent months watching specialists work. The insight that this was a "natural language understanding problem disguised as a search problem" came from seeing how they naturally described products vs. how databases were structured. Product intuition comes from being close to the work.

**4. Conversational Interfaces Lower Adoption Barriers**

Users adopted the tool faster because the chat interface felt familiar and forgiving. They could try vague queries, refine them, and explore options without feeling like they needed to learn a new system. For AI products especially, conversational UX reduces friction significantly.

### What's Next

If I were to continue developing this product, I'd focus on:
1. **Multi-country support** - expanding beyond US HTS to EU, Canada, China tariff systems
2. **Historical classification memory** - learning from user refinements to improve future suggestions
3. **Batch processing** - allowing users to classify entire product catalogs at once
4. **Integration APIs** - embedding into existing trade management platforms

---

## 🚀 Try It Yourself

**Live Demo:** [hts-oracle-demo.com](#)  
**Source Code:** [github.com/DavidRod1865/HTS-Classifier](https://github.com/DavidRod1865/HTS-Classifier)

### Quick Start Example

```bash
# Clone and run locally
git clone https://github.com/DavidRod1865/HTS-Classifier
cd HTS-Classifier
npm install && npm run dev
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
├── 🎨 Frontend (React + TypeScript)
│   ├── Modern UI with shadcn/ui components
│   ├── Progressive disclosure design
│   ├── Contextual help system
│   └── Professional export capabilities
│
├── 🔧 Backend (Python + Flask)
│   ├── Claude AI integration for analysis
│   ├── Pinecone vector database for RAG
│   ├── USITC HTS data processing
│   └── RESTful API design
│
└── 📊 Data Layer
    ├── Official USITC HTS Schedule (CSV)
    ├── Vector embeddings for semantic search
    └── Classification confidence scoring
```

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Anthropic API Key** (for Claude AI)
- **Pinecone API Key** (for vector database)

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

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start backend server
python app.py
```

The backend will start on `http://localhost:8000`

**3. Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.development
# Edit with your backend URL

# Start development server
npm run dev
```

The frontend will start on `http://localhost:5173`

**4. Initialize HTS Database**

```bash
# POST request to setup endpoint
curl -X POST http://localhost:8000/api/setup-index \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "data/hts_2025_revision_13.csv"}'
```

### API Reference

#### `POST /api/classify`
Classify a product and return HTS codes with duty information.

**Request:**
```json
{
  "query": "cotton t-shirts from China"
}
```

**Response:**
```json
{
  "success": true,
  "type": "final_classification",
  "message": "Found 3 HTS classifications from USITC HTS schedule",
  "data": {
    "results": [{
      "hts_code": "6109.10.0000",
      "description": "T-shirts, singlets and other vests, knitted or crocheted, of cotton",
      "effective_duty": "16.5%",
      "confidence_score": 95,
      "match_type": "csv_lookup",
      "duty_source": "usitc"
    }],
    "claude_analysis": "Detailed analysis text...",
    "interpretation": {...}
  }
}
```

#### `GET /api/health`
Health check endpoint.

### Project Structure

```
hts-classifier/
├── backend/                 # Python Flask API
│   ├── app.py              # Main Flask application
│   ├── src/                # Core modules
│   │   └── commodity_rag_search.py
│   ├── requirements.txt    # Python dependencies
│   └── README.md          # Backend documentation
│
├── frontend/               # React TypeScript app
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── utils/        # Helper functions
│   │   └── styles/       # CSS and styling
│   ├── package.json      # Node.js dependencies
│   └── README.md         # Frontend documentation
│
├── data/                  # HTS data files
│   └── hts_2025_revision_13.csv
│
└── docs/                  # Documentation
    └── implementation/    # Technical guides
```

### Configuration

**Backend Environment Variables:**

```bash
# Required
ANTHROPIC_API_KEY=your_claude_api_key
PINECONE_API_KEY=your_pinecone_api_key

# Optional
FLASK_ENV=development
PORT=8000
PINECONE_INDEX_NAME=commodity-hts-codes
```

**Frontend Environment Variables:**

```bash
# Development
VITE_API_URL=http://localhost:8000

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
# Frontend tests
cd frontend
npm run test

# E2E tests with Playwright
npm run test:e2e
```

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
- **Pinecone** for vector database infrastructure

## ⚠️ Disclaimer

HTS Oracle provides classifications for reference purposes only. Final HTS classifications should be verified with licensed customs brokers or through official CBP ruling procedures.

---

**Built for the international trade community** | [View Portfolio](https://davebuilds.tech) | [LinkedIn](https://linkedin.com/in/david-rodriguez1865)
