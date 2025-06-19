"""
HTS Classifier Backend API

Flask API server that provides HTS classification using RAG search with Pinecone and Claude.
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from commodity_rag_search import CommodityRAGSearch, create_hts_index
except ImportError as e:
    print(f"❌ Could not import RAG search modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = FLASK_ENV == 'development'

app = Flask(__name__)

# CORS configuration
if DEBUG:
    # Development origins
    allowed_origins = [
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://localhost:5173", 
        "http://localhost:5174",
        "http://localhost:8000"
    ]
    CORS(app, origins=allowed_origins, supports_credentials=True)
else:
    # Production origins - Allow Netlify and custom domains
    netlify_origin = os.getenv('NETLIFY_URL', '')
    custom_domain = os.getenv('FRONTEND_URL', '')
    
    allowed_origins = []
    
    # Add Netlify deploy preview and production URLs
    if netlify_origin:
        allowed_origins.append(netlify_origin)
    
    # Add custom domain if specified
    if custom_domain:
        allowed_origins.append(custom_domain)
    
    # Fallback patterns for Netlify
    allowed_origins.extend([
        "https://*.netlify.app",
        "https://*.netlify.com"
    ])
    
    # Remove empty strings
    allowed_origins = [origin for origin in allowed_origins if origin]
    
    if allowed_origins:
        CORS(app, origins=allowed_origins, supports_credentials=True)
    else:
        # Fallback: allow all HTTPS origins (less secure but functional)
        CORS(app, origins=["https://*"], supports_credentials=True)

class HTSClassifierAPI:
    """
    Main API class for HTS classification with RAG search
    """
    
    def __init__(self):
        self.rag_search = None
        self.is_ready = False
        self.initialize()
    
    def initialize(self):
        """Initialize the Commodity RAG search system"""
        try:
            # Get API keys from environment
            pinecone_api_key = os.getenv('PINECONE_API_KEY')
            anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not pinecone_api_key:
                logger.error("PINECONE_API_KEY environment variable not set")
                return False
            
            if not anthropic_api_key:
                logger.error("ANTHROPIC_API_KEY environment variable not set")
                return False
            
            logger.info("🔄 Initializing HTS Classifier Commodity RAG Search...")
            
            self.rag_search = CommodityRAGSearch(
                pinecone_api_key=pinecone_api_key,
                anthropic_api_key=anthropic_api_key
            )
            
            self.is_ready = True
            logger.info("✅ HTS Classifier API ready")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize API: {e}")
            return False
    
    def classify_product(self, user_query):
        """
        Classify a product using Commodity RAG search
        
        Args:
            user_query (str): User's product description
            
        Returns:
            dict: Classification results
        """
        if not self.is_ready:
            return {
                "success": False,
                "error": "API not ready - initialization failed"
            }
        
        try:
            logger.info(f"🔍 Processing query: {user_query}")
            
            # Use Commodity RAG search for classification
            result = self.rag_search.search(user_query)
            
            # Format response for frontend
            response = self._format_for_frontend(result, user_query)
            
            logger.info(f"✅ Classification completed for: {user_query}")
            return {
                "success": True,
                **response
            }
            
        except Exception as e:
            logger.error(f"❌ Classification failed: {e}")
            return {
                "success": False,
                "error": f"Classification failed: {str(e)}"
            }
    
    def _get_hts_data_from_csv(self, hts_codes):
        """
        Look up HTS codes in the CSV file to get actual descriptions and duty rates
        
        Args:
            hts_codes (list): List of HTS codes to look up
            
        Returns:
            list: List of formatted results with actual CSV data
        """
        try:
            import pandas as pd
            import os
            
            # Path to CSV file (relative to backend directory)
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'hts_2025_revision_13.csv')
            
            if not os.path.exists(csv_path):
                logger.warning(f"HTS CSV file not found at {csv_path}")
                return []
            
            # Load CSV data
            df = pd.read_csv(csv_path, low_memory=False)
            
            results = []
            for hts_code in hts_codes:
                # Look for exact match or closest match
                matches = df[df['HTS Number'].astype(str) == hts_code]
                
                if matches.empty:
                    # Try partial match (remove trailing zeros)
                    partial_code = hts_code.rstrip('0').rstrip('.')
                    matches = df[df['HTS Number'].astype(str).str.startswith(partial_code)]
                
                if not matches.empty:
                    match_row = matches.iloc[0]  # Take first match
                    
                    # Format HTS code to standard 10-digit format (remove extra dots)
                    csv_hts_code = str(match_row.get('HTS Number', hts_code))
                    formatted_hts_code = self._format_hts_code(csv_hts_code)
                    
                    # Clean up duty information (handle nan values)
                    general_duty = match_row.get('General Rate of Duty', '')
                    special_duty = match_row.get('Special Rate of Duty', '')
                    unit = match_row.get('Unit of Quantity', '')
                    
                    # Convert pandas nan to empty string
                    if pd.isna(general_duty) or str(general_duty).lower() == 'nan':
                        general_duty = 'Free'
                    if pd.isna(special_duty) or str(special_duty).lower() == 'nan':
                        special_duty = ''
                    if pd.isna(unit) or str(unit).lower() == 'nan':
                        unit = ''
                    
                    result = {
                        "hts_code": formatted_hts_code,
                        "description": str(match_row.get('Enhanced Description', 'Description not available')),
                        "effective_duty": str(general_duty),
                        "confidence_score": 90,  # High confidence for exact CSV match
                        "match_type": "csv_lookup",
                        "chapter": formatted_hts_code[:2],
                        "unit": str(unit),
                        "special_duty": str(special_duty),
                        "duty_source": "usitc",
                    }
                    results.append(result)
                # Skip HTS codes that are not found in CSV - only return codes that exist in the official data
            
            return results
            
        except Exception as e:
            logger.error(f"Error looking up HTS data in CSV: {e}")
            return []
    
    def _format_hts_code(self, hts_code):
        """
        Format HTS code to standard 10-digit format (4011.20.1015)
        
        Args:
            hts_code (str): HTS code in various formats
            
        Returns:
            str: Formatted HTS code in standard format
        """
        if not hts_code or str(hts_code).lower() == 'nan':
            return ''
        
        # Remove all dots and format as 10-digit code
        digits_only = ''.join(c for c in str(hts_code) if c.isdigit())
        
        if len(digits_only) >= 10:
            # Format as XXXX.XX.XXXX
            return f"{digits_only[:4]}.{digits_only[4:6]}.{digits_only[6:10]}"
        elif len(digits_only) == 8:
            # Pad with zeros if needed
            digits_only = digits_only + "00"
            return f"{digits_only[:4]}.{digits_only[4:6]}.{digits_only[6:10]}"
        else:
            return str(hts_code)  # Return as-is if format unclear
    
    def _format_rag_results(self, search_result, user_query):
        """
        Format Local RAG search results for React frontend
        
        Args:
            search_result (dict): Results from Local RAG search
            user_query (str): Original user query
            
        Returns:
            dict: Formatted response for frontend
        """
        try:
            interpretation = search_result.get('interpretation', {})
            hts_matches = search_result.get('hts_matches', [])
            final_answer = search_result.get('final_answer', '')
            
            if hts_matches:
                return {
                    "type": "final_classification",
                    "message": f"Found {len(hts_matches)} HTS classification matches using RAG search",
                    "data": {
                        "results": hts_matches,
                        "interpretation": interpretation,
                        "claude_analysis": final_answer
                    }
                }
            else:
                return {
                    "type": "no_results",
                    "message": "No HTS classifications found. Try being more specific about the product.",
                    "data": {
                        "interpretation": interpretation,
                        "claude_analysis": final_answer
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Error formatting RAG results: {e}")
            return {
                "type": "no_results",
                "message": "Error processing classification results",
                "data": {}
            }

    def _format_for_frontend(self, rag_result, user_query):
        """
        Format RAG search results for React frontend
        
        Args:
            rag_result (dict): Results from RAG search
            user_query (str): Original user query
            
        Returns:
            dict: Formatted response for frontend
        """
        try:
            interpretation = rag_result.get('interpretation', {})
            hts_matches = rag_result.get('hts_matches', {})
            final_answer = rag_result.get('final_answer', '')
            
            # Check if we have matches
            if hasattr(hts_matches, 'matches') and hts_matches.matches:
                # Convert Pinecone matches to frontend format
                results = []
                for match in hts_matches.matches[:5]:  # Limit to top 5
                    if hasattr(match, 'metadata'):
                        metadata = match.metadata
                        score = match.score if hasattr(match, 'score') else 0
                        
                        result = {
                            "hts_code": metadata.get('hts_code', ''),
                            "description": metadata.get('description', ''),
                            "effective_duty": metadata.get('general_rate', 'Unknown'),
                            "confidence_score": int(score * 100),  # Convert to percentage
                            "match_type": "rag_search",
                            "chapter": metadata.get('chapter', ''),
                            "unit": metadata.get('unit', ''),
                            "special_duty": metadata.get('special_rate', ''),
                            "duty_source": "pinecone_rag",
                        }
                        results.append(result)
                
                return {
                    "type": "final_classification",
                    "message": f"Found {len(results)} HTS classification matches",
                    "data": {
                        "results": results,
                        "interpretation": interpretation,
                        "claude_analysis": final_answer
                    }
                }
            else:
                # No Pinecone matches, but Claude provided analysis
                # Parse Claude's analysis for HTS codes as fallback
                import re
                hts_codes = re.findall(r'(\d{4}\.\d{2}\.\d{4})', final_answer)
                
                if hts_codes:
                    # Load HTS data from CSV to get actual duty rates and descriptions
                    results = self._get_hts_data_from_csv(hts_codes[:5])
                    
                    if not results:
                        # Fallback if CSV lookup fails
                        results = []
                        for hts_code in hts_codes[:5]:
                            result = {
                                "hts_code": hts_code,
                                "description": "HTS classification identified by AI analysis",
                                "effective_duty": "Not available",
                                "confidence_score": 85,
                                "match_type": "ai_analysis",
                                "chapter": hts_code[:2],
                                "unit": "",
                                "special_duty": "",
                                "duty_source": "usitc",
                            }
                            results.append(result)
                    
                    return {
                        "type": "final_classification",
                        "message": f"Found {len(results)} HTS classifications from USITC HTS schedule",
                        "data": {
                            "results": results,
                            "interpretation": interpretation,
                            "claude_analysis": final_answer
                        }
                    }
                else:
                    return {
                        "type": "no_results",
                        "message": "No HTS classifications found. Try being more specific.",
                        "data": {
                            "interpretation": interpretation,
                            "claude_analysis": final_answer
                        }
                    }
                
        except Exception as e:
            logger.error(f"❌ Error formatting results: {e}")
            return {
                "type": "no_results",
                "message": "Error processing classification results",
                "data": {}
            }

# Initialize API
logger.info("🚀 Starting HTS Classifier API...")
api = HTSClassifierAPI()

@app.route('/api/classify', methods=['POST'])
def classify_product():
    """
    Main classification endpoint
    
    Expected JSON:
    {
        "query": "product description",
        "session_id": "optional_session_id"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON"
            }), 400
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'query' field in request"
            }), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({
                "success": False,
                "error": "Query cannot be empty"
            }), 400
        
        # Process classification
        result = api.classify_product(query)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"❌ API error: {e}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "api_ready": api.is_ready,
        "version": "1.0.0",
        "environment": FLASK_ENV
    })

@app.route('/api/setup-index', methods=['POST'])
def setup_index():
    """
    Setup Pinecone index with HTS data
    
    Expected JSON:
    {
        "csv_path": "path/to/hts/data.csv",
        "index_name": "commodity-hts-codes"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON"
            }), 400
        
        data = request.get_json()
        csv_path = data.get('csv_path', 'data/hts_2025_revision_13.csv')
        index_name = data.get('index_name', 'commodity-hts-codes')
        
        # Get API keys
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        if not pinecone_api_key:
            return jsonify({
                "success": False,
                "error": "PINECONE_API_KEY environment variable required"
            }), 500
        
        # Create and populate index
        success = create_hts_index(pinecone_api_key, csv_path, index_name)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Successfully created and populated index: {index_name}"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create index"
            }), 500
    
    except Exception as e:
        logger.error(f"❌ Setup index error: {e}")
        return jsonify({
            "success": False,
            "error": f"Setup failed: {str(e)}"
        }), 500

@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        "name": "HTS Classifier RAG API",
        "version": "1.0.0",
        "description": "HTS classification using RAG search with Pinecone and Claude",
        "endpoints": {
            "POST /api/classify": "Classify products using RAG search",
            "GET /api/health": "Health check",
            "POST /api/setup-index": "Setup Pinecone index with HTS data"
        },
        "features": [
            "RAG search with Pinecone vector database",
            "Claude AI for query interpretation and synthesis",
            "HTS classification with duty rates",
            "RESTful API design"
        ],
        "status": "ready" if api.is_ready else "not_ready"
    })

if __name__ == '__main__':
    # Get port from environment variable (for deployment)
    port = int(os.environ.get('PORT', 8000))
    
    if DEBUG:
        print("\n" + "="*60)
        print("🤖 HTS Classifier RAG API")
        print("="*60)
        print(f"🔧 API Status: {'✅ Ready' if api.is_ready else '❌ Not Ready'}")
        print("\n📡 API Endpoints:")
        print("   POST /api/classify - Product classification")
        print("   GET  /api/health - Health check")
        print("   POST /api/setup-index - Setup Pinecone index")
        print("\n🎯 Features:")
        print("   ✅ RAG search with Pinecone")
        print("   ✅ Claude AI integration")
        print("   ✅ HTS classification")
        print("   ✅ RESTful API")
        print(f"\n🌐 Running on port: {port}")
        print("="*60)
    
    app.run(
        debug=DEBUG,
        host='0.0.0.0',
        port=port,
        threaded=True
    )