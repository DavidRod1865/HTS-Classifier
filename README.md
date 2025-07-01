# HTS Oracle - AI-Powered Harmonized Tariff Schedule Classifier

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=white)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.9+-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

> Professional-grade HTS classification system using AI and official USITC data to help importers, exporters, and customs professionals classify products accurately.

## 🎯 **Overview**

HTS Oracle is an enterprise-ready web application that leverages AI and official USITC Harmonized Tariff Schedule data to provide accurate product classifications with duty rates, regulatory requirements, and compliance guidance.

### ✨ **Key Features**

- **🤖 AI-Powered Classification**: Uses Claude AI with RAG (Retrieval-Augmented Generation) for intelligent product analysis
- **📊 Official USITC Data**: Direct integration with official U.S. International Trade Commission HTS database
- **📋 Professional Reports**: Export detailed classification reports with duty rates and compliance notes
- **♿ Enterprise Accessibility**: WCAG-compliant interface with screen reader support
- **📱 Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **🔍 Contextual Help**: Comprehensive guidance system for classification best practices
- **⚡ Real-time Processing**: Fast, intelligent classification with confidence scoring

## 🏗️ **Architecture**

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

## 🚀 **Quick Start**

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Anthropic API Key** (for Claude AI)
- **Pinecone API Key** (for vector database)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/hts-oracle.git
cd hts-oracle
```

### 2. Backend Setup

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

### 3. Frontend Setup

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

### 4. Initialize HTS Database (Optional)

To populate the Pinecone vector database with HTS data:

```bash
# POST request to setup endpoint
curl -X POST http://localhost:8000/api/setup-index \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "data/hts_2025_revision_13.csv"}'
```

## 📖 **Usage**

### Basic Classification

1. **Enter Product Description**: Type a detailed product description
2. **Review Results**: Analyze suggested HTS codes with confidence scores
3. **Verify Classification**: Check official USITC data and regulatory notes
4. **Export Report**: Generate professional HTML reports for customs documentation

### Example Queries

```
✅ Good: "100% cotton knitted t-shirts for men"
✅ Good: "Stainless steel pipes for construction, 2-inch diameter"
✅ Good: "LED light bulbs, 60-watt equivalent, household use"

❌ Avoid: "Nike shirts" (brand names)
❌ Avoid: "Machine parts" (too vague)
❌ Avoid: "Stuff from China" (not descriptive)
```

### API Usage

```bash
# Classify a product
curl -X POST http://localhost:8000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "cotton t-shirts from China"}'

# Health check
curl http://localhost:8000/api/health
```

## 🛠️ **Development**

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
│   │   │   ├── layout/   # Header, Layout components
│   │   │   ├── search/   # Search form components
│   │   │   ├── results/  # Results display components
│   │   │   └── shared/   # Shared utilities
│   │   ├── utils/        # Helper functions
│   │   └── styles/       # CSS and styling
│   ├── package.json      # Node.js dependencies
│   └── README.md         # Frontend documentation
│
├── data/                  # HTS data files
│   └── hts_2025_revision_13.csv
│
├── tests/                 # End-to-end tests
│   ├── accessibility.spec.js
│   ├── basic.spec.js
│   └── e2e-classification.spec.js
│
└── docs/                  # Documentation
    └── implementation/    # Technical guides
```

### Running Tests

```bash
# Frontend tests
cd frontend
npm run test

# E2E tests with Playwright
npm run test:e2e

# Accessibility tests
npm run test:accessibility
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

## 🔧 **Configuration**

### Backend Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your_claude_api_key
PINECONE_API_KEY=your_pinecone_api_key

# Optional
FLASK_ENV=development
PORT=8000
PINECONE_INDEX_NAME=commodity-hts-codes
PINECONE_DIMENSION=50
```

### Frontend Environment Variables

```bash
# Development
VITE_API_URL=http://localhost:8000

# Production
VITE_API_URL=https://your-api-domain.com
```

## 📊 **API Reference**

### Endpoints

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

#### `POST /api/setup-index`
Initialize and populate the Pinecone vector database.

## 🎨 **Design System**

### Typography Scale
- **H1**: 36px (Main titles)
- **H2**: 30px (Section headers)
- **H3**: 24px (Card titles)
- **Body**: 16px (Content)
- **Small**: 14px (Metadata)

### Color Palette
- **Primary**: Blue 600 (#2563eb)
- **Success**: Green 600 (#16a34a)
- **Warning**: Amber 500 (#f59e0b)
- **Error**: Red 600 (#dc2626)
- **Neutral**: Gray scale

### Spacing System
- **XS**: 8px, **SM**: 12px, **MD**: 16px
- **LG**: 24px, **XL**: 32px, **2XL**: 48px

## ♿ **Accessibility**

HTS Oracle is built with accessibility as a priority:

- **WCAG 2.1 AA compliant**
- **Keyboard navigation** for all features
- **Screen reader support** with proper ARIA labels
- **Focus management** and visual indicators
- **High contrast mode** compatibility
- **Reduced motion** support

## 📱 **Browser Support**

- **Chrome** 90+
- **Firefox** 88+
- **Safari** 14+
- **Edge** 90+

## 🔒 **Security**

- **API key protection** with environment variables
- **CORS configuration** for cross-origin requests
- **Input validation** and sanitization
- **No sensitive data logging**

## 📈 **Performance**

- **Code splitting** for optimal loading
- **Lazy loading** of components
- **Optimized bundle size**
- **Responsive images**
- **Caching strategies**

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow TypeScript best practices
- Write tests for new features
- Ensure accessibility compliance
- Update documentation
- Follow the established code style

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **USITC** for providing official HTS schedule data
- **Anthropic** for Claude AI capabilities
- **Pinecone** for vector database infrastructure
- **shadcn/ui** for the beautiful component system

## 📞 **Support**

For support, please:

1. Check the [Documentation](./docs/)
2. Search existing [Issues](https://github.com/yourusername/hts-oracle/issues)
3. Create a new issue with detailed information

## ⚠️ **Disclaimer**

HTS Oracle provides classifications for reference purposes only. Final HTS classifications should be verified with licensed customs brokers or through official CBP ruling procedures. Duty rates and regulations are subject to change.

---

**Built with ❤️ for the international trade community**