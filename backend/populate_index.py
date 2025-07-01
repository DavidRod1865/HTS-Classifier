#!/usr/bin/env python3
"""
Script to populate Pinecone index with HTS data
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')

from commodity_rag_search import create_hts_index

def main():
    pinecone_api_key = os.getenv('PINECONE_API_KEY')
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not pinecone_api_key:
        print("❌ PINECONE_API_KEY not found in environment")
        return False
        
    if not anthropic_api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        return False
    
    print("🚀 Starting Pinecone index population...")
    
    # Use relative path to data
    csv_path = '../data/hts_2025_revision_13.csv'
    index_name = 'commodity-hts-codes'
    
    success = create_hts_index(pinecone_api_key, csv_path, index_name)
    
    if success:
        print("✅ Successfully populated Pinecone index!")
        return True
    else:
        print("❌ Failed to populate index")
        return False

if __name__ == "__main__":
    main()