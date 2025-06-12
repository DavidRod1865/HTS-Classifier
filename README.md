# HTS Classification System

A sophisticated, AI-powered system for classifying products under the Harmonized Tariff Schedule (HTS) codes using LangGraph workflows and Claude AI.

## 🚀 Features

- **Intelligent Product Classification**: Advanced AI-driven HTS code classification
- **Conversational Interface**: Interactive clarifying questions for accurate results
- **Multiple Search Strategies**: Exact match, fuzzy search, and semantic search
- **High Confidence Scoring**: Confidence-based result filtering and presentation
- **Turn-Limited Conversations**: Structured 3-turn conversation workflow
- **RESTful API**: Complete Flask-based API with CORS support
- **Modular Architecture**: Clean, maintainable codebase with separation of concerns

## 📁 Project Structure

```
hts-classifier/
├── src/                          # Core application modules
│   ├── constants.py             # Configuration constants and mappings
│   ├── config.py                # Configuration management
│   ├── csv_hts_loader.py        # HTS data loading and management
│   ├── search_engine.py         # Multi-strategy HTS search engine
│   ├── question_generator.py    # AI-powered question generation
│   ├── product_classifier.py    # Product classification logic
│   ├── langgraph_hts_agent.py   # Main LangGraph workflow agent
│   ├── basic_classifier.py      # Basic classification utilities
│   ├── conversational_classifier.py # Conversational interfaces
│   ├── hts_classifier.py        # Legacy classifier
│   └── __init__.py
├── data/                        # HTS data files
│   └── hts_2025_revision_13.csv # HTS tariff data
├── frontend/                    # React frontend application
├── archive/                     # Archived/legacy files
├── app.py                       # Flask API server
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd hts-classifier
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   export LOG_LEVEL="INFO"  # Optional
   export FLASK_DEBUG="True"  # Optional, for development
   ```

## 🚀 Usage

### API Server

Start the Flask API server:

```bash
python app.py
```

The API will be available at `http://localhost:8000` with the following endpoints:

- `POST /api/classify` - Classify products with conversation support
- `POST /api/session/clear` - Clear conversation session
- `GET /api/health` - Health check
- `GET /api/capabilities` - Get API capabilities

### Direct Usage

Use the agent directly in Python:

```python
from src.langgraph_hts_agent import LangGraphHTSAgent

# Initialize the agent
agent = LangGraphHTSAgent()
if not agent.initialize():
    print("Failed to initialize agent")
    exit(1)

# Classify a product
result = agent.classify_commodity("rubber tires for trucks")

if result["success"]:
    state = result["result"]
    print(f"Classification: {state.get('final_classification')}")
else:
    print(f"Error: {result['error']}")
```

### API Usage Examples

**Basic Classification**:
```bash
curl -X POST http://localhost:8000/api/classify \\
  -H "Content-Type: application/json" \\
  -d '{"query": "laptop computer", "session_id": "test-session"}'
```

**Continue Conversation**:
```bash
curl -X POST http://localhost:8000/api/classify \\
  -H "Content-Type: application/json" \\
  -d '{"query": "It is made of aluminum", "session_id": "test-session"}'
```

## 🏗️ Architecture

### Core Components

1. **LangGraph Agent** (`langgraph_hts_agent.py`):
   - Main workflow orchestrator using LangGraph
   - Manages conversation state and decision flow
   - Coordinates between all other components

2. **Search Engine** (`search_engine.py`):
   - Multi-strategy search implementation
   - Exact match, fuzzy search, and semantic search
   - Relevance scoring and result filtering

3. **Question Generator** (`question_generator.py`):
   - AI-powered clarifying question generation
   - Context-aware questions based on search results
   - Turn-based conversation management

4. **Product Classifier** (`product_classifier.py`):
   - Product confirmation and understanding
   - Final classification result formatting
   - Option selection and validation

5. **Configuration Management** (`config.py`, `constants.py`):
   - Centralized configuration and constants
   - Environment-based configuration
   - Validation and reporting

### Workflow

1. **Product Confirmation**: Claude AI confirms understanding of the product
2. **Hierarchy Search**: Multi-strategy search for matching HTS codes
3. **Decision Logic**: Based on results, either ask questions or classify
4. **Clarifying Questions**: Up to 3 turns of intelligent questions
5. **Final Classification**: Present high-confidence results or top options
6. **User Selection**: Handle user selection from multiple options

## 🔧 Configuration

### Environment Variables

- `ANTHROPIC_API_KEY`: Required. Your Anthropic API key
- `LOG_LEVEL`: Optional. Logging level (DEBUG, INFO, WARNING, ERROR)
- `FLASK_DEBUG`: Optional. Enable Flask debug mode

### Configuration Files

- `src/constants.py`: All configuration constants and mappings
- `src/config.py`: Configuration management and validation

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# Run tests with coverage
pytest --cov=src
```

Test the agent directly:

```bash
cd src
python langgraph_hts_agent.py
```

## 📊 Features in Detail

### Search Strategies

1. **Exact Text Search**: Direct text matching in HTS descriptions
2. **Fuzzy Search**: Similarity-based matching with configurable thresholds
3. **Semantic Search**: Context-aware search using product keywords
4. **Chapter-Targeted Search**: Product-specific chapter focusing

### Confidence Scoring

- **High Confidence** (≥85%): Direct classification or option presentation
- **Medium Confidence** (70-84%): Clarifying questions to improve accuracy
- **Low Confidence** (<70%): Additional questions or fallback options

### Conversation Management

- **Turn Limits**: Maximum 3 clarifying questions per session
- **Context Preservation**: Maintains conversation history
- **Session Management**: Multi-session support with state isolation

## 🔄 API Response Types

- `clarifying_questions`: Questions to gather more information
- `final_classification`: Single classification result
- `multiple_options`: Multiple options for user selection
- `high_confidence_results`: High-confidence matches
- `low_confidence_results`: Lower confidence potential matches
- `no_results`: No suitable matches found

## 📈 Performance Optimizations

- **Modular Architecture**: Separation of concerns for maintainability
- **Efficient Search**: Multi-strategy search with early termination
- **Caching**: Search result caching (in search engine)
- **Lazy Loading**: Components initialized only when needed
- **Memory Management**: Efficient pandas operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the configuration with `config.validate_and_report()`
2. Review logs for error details
3. Ensure all dependencies are properly installed
4. Verify your Anthropic API key is valid

## 🔮 Future Enhancements

- [ ] Embeddings-based semantic search
- [ ] Machine learning model integration
- [ ] Advanced caching strategies
- [ ] Performance monitoring and analytics
- [ ] Additional data sources integration
- [ ] Batch processing capabilities