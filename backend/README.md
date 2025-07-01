# HTS Oracle Backend API

Flask-based REST API that provides HTS (Harmonized Tariff Schedule) classification using RAG (Retrieval-Augmented Generation) with Pinecone vector database and Anthropic Claude AI.

## 🏗️ **Architecture**

The backend implements a sophisticated RAG pipeline:

```
User Query → Claude AI Interpretation → Vector Search → Claude Analysis → Structured Response
```

### Components

- **Flask API**: RESTful endpoints for classification and management
- **RAG Pipeline**: Advanced retrieval-augmented generation system
- **Claude AI**: Query interpretation and synthesis
- **Pinecone**: Vector database for semantic search
- **USITC Data**: Official HTS classification database

## 🚀 **Quick Start**

### Prerequisites

- Python 3.8+
- Anthropic API Key
- Pinecone API Key

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Create `.env` file with:

```bash
# Required API Keys
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
PINECONE_API_KEY=your-pinecone-key-here

# Optional Configuration
FLASK_ENV=development
PORT=8000
PINECONE_INDEX_NAME=commodity-hts-codes
PINECONE_DIMENSION=50
```

### Running

```bash
# Development server (with auto-reload)
python app.py

# Production server
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Server starts at `http://localhost:8000`

## 📡 **API Endpoints**

### Classification

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
    "results": [
      {
        "hts_code": "6109.10.0000",
        "description": "T-shirts, singlets and other vests, knitted or crocheted, of cotton",
        "effective_duty": "16.5%",
        "confidence_score": 95,
        "match_type": "csv_lookup",
        "chapter": "61",
        "unit": "Dozen",
        "special_duty": "Free (AU,BH,CL,CO,D,E,IL,JO,KR,MA,OM,P,PA,PE,S,SG)",
        "duty_source": "usitc"
      }
    ],
    "interpretation": {
      "commodity_type": "textiles",
      "specific_product": "cotton t-shirts",
      "search_terms": ["cotton t-shirts", "textile apparel"],
      "intent": "classification"
    },
    "claude_analysis": "Detailed AI analysis of the classification..."
  }
}
```

### Management

#### `GET /api/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "api_ready": true,
  "version": "1.0.0",
  "environment": "development"
}
```

#### `POST /api/setup-index`

Initialize and populate Pinecone index with HTS data.

**Request:**
```json
{
  "csv_path": "data/hts_2025_revision_13.csv",
  "index_name": "commodity-hts-codes"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully created and populated index: commodity-hts-codes"
}
```

## 🧠 **RAG Pipeline**

### Stage 1: Query Interpretation

Claude AI analyzes the user query to extract:
- Commodity type
- Specific product details
- HTS-relevant keywords
- Search optimization terms
- User intent

### Stage 2: Vector Search

Pinecone performs semantic search using:
- Claude-generated embeddings
- Filtered searches by commodity type
- Confidence scoring
- Metadata filtering

### Stage 3: Analysis & Synthesis

Claude AI synthesizes results into:
- Most relevant HTS codes
- Duty rate analysis
- Regulatory requirements
- Classification confidence
- Compliance guidance

## 🗄️ **Data Processing**

### HTS Data Structure

The system processes official USITC HTS data with:

```python
{
  "hts_code": "6109.10.0000",
  "description": "Enhanced product description",
  "context_path": "Hierarchical classification path",
  "search_keywords": "Optimized search terms",
  "commodity_type": "textiles",
  "chapter": "61",
  "general_rate": "16.5%",
  "special_rate": "Free (AU,BH,CL...)",
  "unit": "Dozen"
}
```

### Vector Embeddings

The system creates embeddings from:
- Product descriptions
- Classification context
- Search keywords
- Hierarchical paths

## 🔧 **Configuration Options**

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude AI API key | Required |
| `PINECONE_API_KEY` | Pinecone API key | Required |
| `FLASK_ENV` | Environment mode | `development` |
| `PORT` | Server port | `8000` |
| `PINECONE_INDEX_NAME` | Index name | `commodity-hts-codes` |
| `PINECONE_DIMENSION` | Vector dimension | `50` |

### CORS Configuration

Development origins:
- `http://localhost:3000`
- `http://localhost:5173`
- `http://localhost:8000`

Production origins configured via environment.

## 🧪 **Development**

### Project Structure

```
backend/
├── app.py                    # Main Flask application
├── src/
│   ├── __init__.py
│   └── commodity_rag_search.py  # RAG implementation
├── requirements.txt          # Dependencies
├── run.py                   # Development runner
├── check_index.py           # Pinecone diagnostics
├── .env.example             # Environment template
└── README.md               # This file
```

### Key Classes

#### `HTSClassifierAPI`
Main API class handling:
- Request processing
- Response formatting
- Error handling
- State management

#### `CommodityRAGSearch`
Core RAG implementation:
- Query interpretation
- Vector search
- Result synthesis
- Embedding generation

### Development Commands

```bash
# Start development server
python app.py

# Check Pinecone index status
python check_index.py

# Setup/reset Pinecone index
curl -X POST http://localhost:8000/api/setup-index \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "../data/hts_2025_revision_13.csv"}'

# Test classification
curl -X POST http://localhost:8000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "cotton t-shirts"}'
```

## 📊 **Monitoring & Debugging**

### Logging

The application provides detailed logging:

```python
INFO:__main__:🚀 Starting HTS Classifier API...
INFO:__main__:🔄 Initializing HTS Classifier RAG Search...
INFO:__main__:✅ HTS Classifier API ready
INFO:__main__:🔍 Processing query: cotton t-shirts
INFO:__main__:✅ Classification completed for: cotton t-shirts
```

### Health Monitoring

Monitor API health via `/api/health` endpoint for:
- API readiness status
- Component initialization
- Version information
- Environment details

### Error Handling

Comprehensive error handling for:
- Invalid requests
- API failures
- Database connectivity
- Authentication errors

## 🔒 **Security**

### API Key Protection

- Environment variable storage
- No key logging
- Secure transmission

### Input Validation

- Request format validation
- Query sanitization
- Parameter checking
- Error boundary handling

### CORS Security

- Configurable origins
- Credential support
- Method restrictions
- Header validation

## 📈 **Performance**

### Optimization Features

- **Caching**: Intelligent result caching
- **Connection Pooling**: Efficient database connections
- **Async Processing**: Non-blocking operations
- **Error Recovery**: Graceful degradation

### Scaling Considerations

- **Horizontal Scaling**: Multiple worker processes
- **Load Balancing**: Stateless design
- **Database Optimization**: Efficient vector operations
- **Memory Management**: Optimized embeddings

## 🐛 **Troubleshooting**

### Common Issues

1. **API Keys Not Set**
   ```bash
   ERROR: ANTHROPIC_API_KEY environment variable not set
   ```
   Solution: Configure `.env` file with valid API keys

2. **Pinecone Index Not Found**
   ```bash
   WARNING: Pinecone index 'commodity-hts-codes' not found
   ```
   Solution: Run `/api/setup-index` endpoint

3. **Port Already in Use**
   ```bash
   Address already in use
   ```
   Solution: Change PORT in `.env` or kill existing process

### Debug Commands

```bash
# Check Pinecone status
python check_index.py

# Test API connectivity
curl http://localhost:8000/api/health

# View detailed logs
tail -f backend.log
```

## 📦 **Dependencies**

### Core Dependencies

- **flask==3.0.0**: Web framework
- **flask-cors==4.0.0**: CORS handling
- **anthropic>=0.54.0**: Claude AI client
- **pinecone==7.2.0**: Vector database
- **pandas==2.2.3**: Data processing

### Development Dependencies

- **python-dotenv==1.0.0**: Environment management
- **gunicorn==21.2.0**: Production server
- **pytest==7.4.4**: Testing framework

## 🚀 **Deployment**

### Production Setup

```bash
# Install production dependencies
pip install -r requirements.txt

# Set production environment
export FLASK_ENV=production

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

### Environment Configuration

Production environment variables:
- Set `FLASK_ENV=production`
- Configure production CORS origins
- Use secure API key storage
- Enable monitoring and logging

---

For frontend integration, see [Frontend README](../frontend/README.md)