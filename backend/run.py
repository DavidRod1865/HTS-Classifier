#!/usr/bin/env python3
"""
Development server runner for HTS Classifier API
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import and run the Flask app
if __name__ == '__main__':
    from app import app
    
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"🚀 Starting HTS Classifier API on port {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🌐 API will be available at: http://localhost:{port}")
    
    app.run(
        debug=debug,
        host='0.0.0.0',
        port=port,
        threaded=True
    )