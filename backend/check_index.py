#!/usr/bin/env python3
"""
Check Pinecone index status and data
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()

def check_pinecone_index():
    """Check if Pinecone index exists and has data"""
    
    pinecone_api_key = os.getenv('PINECONE_API_KEY')
    if not pinecone_api_key:
        print("❌ Error: PINECONE_API_KEY environment variable not set")
        return
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=pinecone_api_key)
        
        # List indexes
        indexes = [idx.name for idx in pc.list_indexes()]
        print(f"📋 Available indexes: {indexes}")
        
        index_name = "commodity-hts-codes"
        if index_name not in indexes:
            print(f"❌ Index '{index_name}' does not exist!")
            print("Run the following to create it:")
            print("python -c \"from src.commodity_rag_search import create_hts_index; import os; create_hts_index(os.getenv('PINECONE_API_KEY'), '../data/hts_2025_revision_13.csv')\"")
            return
        
        # Get index
        index = pc.Index(index_name)
        
        # Get index stats
        stats = index.describe_index_stats()
        print(f"📊 Index '{index_name}' stats:")
        print(f"   - Total vectors: {stats.total_vector_count}")
        print(f"   - Dimension: {stats.dimension}")
        
        if stats.total_vector_count == 0:
            print("⚠️  Index is empty! No vectors uploaded yet.")
            print("Run the setup-index endpoint to populate it.")
        else:
            print("✅ Index has data and is ready to use!")
            
            # Test a simple query
            print("\n🧪 Testing a simple query...")
            test_embedding = [0.1] * stats.dimension  # Dummy embedding
            results = index.query(
                vector=test_embedding,
                top_k=3,
                include_metadata=True
            )
            
            print(f"📋 Test query returned {len(results.matches)} results")
            for i, match in enumerate(results.matches[:2]):
                print(f"   {i+1}. HTS: {match.metadata.get('hts_code', 'N/A')} (score: {match.score:.3f})")
        
    except Exception as e:
        print(f"❌ Error checking index: {e}")

if __name__ == "__main__":
    print("🔍 Checking Pinecone index status...")
    check_pinecone_index()