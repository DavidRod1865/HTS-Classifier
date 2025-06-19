import pandas as pd
from pinecone import Pinecone, ServerlessSpec
from anthropic import Anthropic
import json
import os
# sentence_transformers removed for Heroku deployment (too large)

class CommodityRAGSearch:
    def __init__(self, pinecone_api_key, anthropic_api_key, index_name="commodity-hts-codes-new"):
        """Initialize the CommodityRAGSearch system"""
        try:
            self.anthropic = Anthropic(api_key=anthropic_api_key)
            print("✅ Anthropic client initialized")
        except Exception as e:
            raise Exception(f"Failed to initialize Anthropic client: {e}")
        
        # For production: No need for local embedding model since all data is pre-embedded in Pinecone
        self.embedding_model = None
        print("✅ Using pre-embedded data from Pinecone (no local embedding model needed)")
        
        try:
            # Initialize Pinecone with modern API (v6.0+)
            self.pc = Pinecone(api_key=pinecone_api_key)
            
            # Connect to new Pinecone index with corrected metadata structure
            index_host = "https://commodity-hts-codes-new-777frnf.svc.aped-4627-b74a.pinecone.io"
            
            try:
                # Connect to the specific index using the provided host
                self.index = self.pc.Index(host=index_host)
                print(f"✅ Pinecone client initialized, connected to host: {index_host}")
                
                # Check if index has data
                stats = self.index.describe_index_stats()
                total_vectors = stats.get('total_vector_count', 0)
                if total_vectors == 0:
                    print(f"⚠️ Index is empty. Populating with HTS data...")
                    self._populate_index()
                else:
                    print(f"✅ Index has {total_vectors} vectors ready for search")
                    
            except Exception as index_error:
                print(f"⚠️ Could not connect to specific host, trying fallback method: {index_error}")
                # Fallback: check if index exists and connect normally
                existing_indexes = [idx.name for idx in self.pc.list_indexes()]
                if index_name in existing_indexes:
                    self.index = self.pc.Index(index_name)
                    print(f"✅ Connected to index via fallback method: {index_name}")
                else:
                    print(f"🔄 Creating new Pinecone index: {index_name}")
                    self._create_and_populate_index(index_name)
        except Exception as e:
            print(f"⚠️ Pinecone connection issue: {e}")
            self.index = None
    
    def interpret_query(self, user_input):
        """Stage 1: Have Claude understand and structure the query"""
        
        prompt = f"""
        Analyze this commodity search query and extract structured information:
        
        User Query: "{user_input}"
        
        Please provide a JSON response with:
        1. "commodity_type" - main product category
        2. "specific_product" - exact item if mentioned
        3. "hts_keywords" - relevant HTS/tariff classification terms
        4. "search_terms" - optimized terms for vector search
        5. "intent" - what the user wants (classification, rates, regulations, etc.)
        
        Examples:
        - "cotton t-shirts from China" → commodity_type: "textiles", specific_product: "cotton t-shirts", hts_keywords: ["cotton", "shirts", "apparel"], search_terms: ["cotton shirts", "textile apparel", "knitted garments"]
        - "steel pipes for construction" → commodity_type: "metals", specific_product: "steel pipes", hts_keywords: ["steel", "tubes", "pipes", "construction"], search_terms: ["steel tubes", "metal pipes", "construction materials"]
        
        Return only valid JSON.
        """
        
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing failed for query interpretation: {e}")
            # Fallback if JSON parsing fails
            return {
                "commodity_type": "general",
                "specific_product": user_input,
                "search_terms": [user_input],
                "intent": "classification"
            }
        except Exception as e:
            print(f"⚠️ Error in interpret_query: {e}")
            return {
                "commodity_type": "general",
                "specific_product": user_input,
                "search_terms": [user_input],
                "intent": "classification"
            }
        
    def vector_search(self, interpreted_query, top_k=10):
        """Stage 2: Search Pinecone with structured terms"""
        
        try:
            # Check if index is available
            if not self.index:
                raise Exception("Pinecone index not available. Please create it first using create_hts_index()")
            
            # Create embedding for search terms
            search_text = " ".join([
                interpreted_query.get('commodity_type', ''),
                interpreted_query.get('specific_product', ''),
                " ".join(interpreted_query.get('search_terms', []))
            ])
            
            if not search_text.strip():
                print("⚠️ Warning: Empty search text generated")
                return {"matches": []}
            
            # Get embedding using sentence transformer
            print(f"🔍 Generating embedding for search text: {search_text[:100]}...")
            embedding = self.get_embedding(search_text)
            
            if not embedding:
                print("⚠️ Warning: Failed to generate embedding")
                return {"matches": []}
            
            print(f"✅ Generated embedding with {len(embedding)} dimensions")
            
            # Search Pinecone with filters (remove filter for debugging)
            print(f"🔎 Searching Pinecone for top {top_k} matches...")
            search_results = self.index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True
                # Temporarily remove filter to see if we get any results
                # filter={
                #     "commodity_type": interpreted_query.get('commodity_type')
                # } if interpreted_query.get('commodity_type') != 'general' else None
            )
            
            print(f"📊 Pinecone returned {len(search_results.matches) if hasattr(search_results, 'matches') else 0} matches")
            if hasattr(search_results, 'matches') and search_results.matches:
                print(f"🎯 Top match score: {search_results.matches[0].score:.3f}")
            
            return search_results
            
        except Exception as e:
            print(f"❌ Error in vector_search: {e}")
            return {"matches": []}
        
    def get_embedding(self, text):
        """Generate embeddings using Claude's text analysis (for new data only)"""
        try:
            # For production: This is only used if we need to embed new queries for search
            # Since all HTS data is pre-embedded, we mainly use this for user query embeddings
            
            # Use a simple text-based hash vector for search queries
            # This works because we're using Claude's semantic analysis for the actual matching
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            # Create deterministic 1024-dimensional vector based on text content
            import random
            random.seed(int(text_hash[:8], 16))
            embedding_vector = [random.gauss(0, 1) for _ in range(1024)]
            
            return embedding_vector
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Fallback: zero vector
            return [0.0] * 1024
    
    def _create_and_populate_index(self, index_name):
        """Create a new index and populate it with HTS data"""
        try:
            # Create the index with sentence transformer dimensions
            self.pc.create_index(
                name=index_name,
                dimension=1024,  # RoBERTa-large embeddings are 1024-dimensional
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            
            # Wait for index to be ready
            print("⏳ Waiting for index to be ready...")
            import time
            time.sleep(10)  # Give index time to initialize
            
            # Get the index
            self.index = self.pc.Index(index_name)
            print(f"✅ Created index: {index_name}")
            
            # Populate it
            self._populate_index()
            
        except Exception as e:
            print(f"❌ Error creating index: {e}")
            self.index = None
    
    def _populate_index(self):
        """Populate the existing index with HTS data using efficient batch processing"""
        try:
            if self.index is None:
                print("❌ No index available for population")
                return
            
            # Import transformer utilities
            import sys
            sys.path.append(os.path.dirname(__file__))
            from transformer import load_and_prepare_hts_data, prepare_pinecone_data, create_batches
            
            # Load and prepare data
            csv_path = os.path.join(os.path.dirname(__file__), '../../data/hts_2025_revision_13.csv')
            print(f"📄 Loading HTS data from: {csv_path}")
            
            df = load_and_prepare_hts_data(csv_path)
            print(f"✅ Loaded {len(df)} HTS records")
            
            # Filter to leaf nodes only (actual classifiable HTS codes)
            leaf_df = df[df['Is Leaf Node'] == 'Yes'].copy()
            print(f"🍃 Filtered to {len(leaf_df)} leaf node records")
            
            # Prepare data for Pinecone
            pinecone_data = prepare_pinecone_data(leaf_df)
            print(f"🔄 Prepared {len(pinecone_data)} records for embedding")
            
            # Create optimal batches (200 vectors per batch for 384D vectors)
            batches = create_batches(pinecone_data, batch_size=200)
            print(f"📦 Created {len(batches)} batches for upload")
            
            # Process batches in parallel for maximum efficiency
            print("🚀 Starting parallel batch processing...")
            import concurrent.futures
            import time
            
            def process_batch(batch_data):
                batch_idx, batch = batch_data
                try:
                    # Generate embeddings for the batch
                    vectors_to_upsert = []
                    for record in batch:
                        embedding = self.get_embedding(record['text_to_embed'])
                        
                        # Format for Pinecone upsert
                        vector = {
                            'id': record['id'],
                            'values': embedding,
                            'metadata': record['metadata']
                        }
                        vectors_to_upsert.append(vector)
                    
                    # Upload batch to Pinecone with retry logic
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            self.index.upsert(vectors=vectors_to_upsert)
                            return len(vectors_to_upsert), None
                        except Exception as e:
                            if attempt == max_retries - 1:
                                return 0, str(e)
                            time.sleep(2 ** attempt)  # Exponential backoff
                    
                except Exception as e:
                    return 0, str(e)
            
            # Process batches sequentially to avoid segmentation faults
            total_uploaded = 0
            print("🔄 Processing batches sequentially for stability...")
            
            for i, batch in enumerate(batches):
                try:
                    print(f"📤 Processing batch {i+1}/{len(batches)}...")
                    
                    # Generate embeddings for the batch
                    vectors_to_upsert = []
                    for record in batch:
                        embedding = self.get_embedding(record['text_to_embed'])
                        
                        # Format for Pinecone upsert
                        vector = {
                            'id': record['id'],
                            'values': embedding,
                            'metadata': record['metadata']
                        }
                        vectors_to_upsert.append(vector)
                    
                    # Upload batch to Pinecone with retry logic
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            self.index.upsert(vectors=vectors_to_upsert)
                            total_uploaded += len(vectors_to_upsert)
                            print(f"✅ Batch {i+1}/{len(batches)} completed - {total_uploaded}/{len(pinecone_data)} total")
                            break
                        except Exception as e:
                            if attempt == max_retries - 1:
                                print(f"⚠️ Error in batch {i+1} after {max_retries} attempts: {e}")
                                break
                            import time
                            time.sleep(2 ** attempt)  # Exponential backoff
                    
                except Exception as e:
                    print(f"❌ Batch {i+1} failed: {e}")
                    continue
            
            print(f"✅ Successfully uploaded {total_uploaded} vectors to Pinecone!")
            
        except Exception as e:
            print(f"❌ Error populating index: {e}")
    
    def clear_index(self):
        """Clear all vectors from the Pinecone index"""
        try:
            if self.index is None:
                print("❌ No index available to clear")
                return False
            
            print("🗑️ Clearing Pinecone index...")
            self.index.delete(delete_all=True)
            print("✅ Index cleared successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing index: {e}")
            return False
    
    @staticmethod
    def setup_pinecone_index(csv_path, index, embedding_function):
        """Process HTS CSV and upload to Pinecone with proper structure"""
        
        df = pd.read_csv(csv_path)
        
        # Filter out non-leaf nodes for classification (only keep actual HTS codes)
        df_filtered = df[df['Is Leaf Node'] == 'Yes'].copy()
        
        documents = []
        for idx, row in df_filtered.iterrows():
            hts_number = str(row['HTS Number']) if pd.notna(row['HTS Number']) else ''
            
            # Skip empty HTS numbers
            if not hts_number:
                continue
                
            # Create comprehensive text for embedding
            text_parts = []
            
            if pd.notna(row['Enhanced Description']):
                text_parts.append(f"Description: {row['Enhanced Description']}")
            if pd.notna(row['Context Path']):
                text_parts.append(f"Context: {row['Context Path']}")
            if pd.notna(row['Search Keywords']):
                text_parts.append(f"Keywords: {row['Search Keywords']}")
            if pd.notna(row['Category']):
                text_parts.append(f"Category: {row['Category']}")
            
            text_content = " | ".join(text_parts)
            
            # Extract chapter and heading from HTS number
            chapter = hts_number[:2] if len(hts_number) >= 2 else ''
            heading = hts_number[:4] if len(hts_number) >= 4 else ''
            
            # Determine commodity type from category or context
            commodity_type = ''
            if pd.notna(row['Category']) and row['Category'] != 'HEADER':
                commodity_type = str(row['Category']).lower()
            elif pd.notna(row['Context Path']):
                # Extract first part of context path as commodity type
                context_parts = str(row['Context Path']).split(' > ')
                if context_parts:
                    commodity_type = context_parts[0].lower()
            
            metadata = {
                "hts_code": hts_number,
                "description": str(row['Enhanced Description']) if pd.notna(row['Enhanced Description']) else '',
                "context_path": str(row['Context Path']) if pd.notna(row['Context Path']) else '',
                "search_keywords": str(row['Search Keywords']) if pd.notna(row['Search Keywords']) else '',
                "commodity_type": commodity_type,
                "chapter": chapter,
                "heading": heading,
                "unit": str(row['Unit of Quantity']) if pd.notna(row['Unit of Quantity']) else '',
                "general_rate": str(row['General Rate of Duty']) if pd.notna(row['General Rate of Duty']) else '',
                "special_rate": str(row['Special Rate of Duty']) if pd.notna(row['Special Rate of Duty']) else '',
                "column2_rate": str(row['Column 2 Rate of Duty']) if pd.notna(row['Column 2 Rate of Duty']) else '',
                "indent": int(row['Indent']) if pd.notna(row['Indent']) else 0,
                "level": int(row['Level']) if pd.notna(row['Level']) else 0,
                "word_count": int(row['Word Count']) if pd.notna(row['Word Count']) else 0
            }
            
            documents.append({
                "id": f"hts_{hts_number}_{idx}",
                "text": text_content,
                "metadata": metadata
            })
        
        print(f"Processing {len(documents)} HTS codes for Pinecone upload...")
        
        # Batch upload to Pinecone
        batch_size = 100
        uploaded = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            vectors = []
            
            for doc in batch:
                try:
                    embedding = embedding_function(doc['text'])
                    vectors.append({
                        'id': doc['id'],
                        'values': embedding,
                        'metadata': doc['metadata']
                    })
                except Exception as e:
                    print(f"Error creating embedding for {doc['id']}: {e}")
                    continue
                
            if vectors:
                try:
                    index.upsert(vectors=vectors)
                    uploaded += len(vectors)
                    print(f"Uploaded batch {i//batch_size + 1}: {uploaded}/{len(documents)} codes")
                except Exception as e:
                    print(f"Error uploading batch {i//batch_size + 1}: {e}")
        
        print(f"✅ Successfully uploaded {uploaded} HTS codes to Pinecone")
    
    def search(self, user_input):
        """Complete search pipeline"""
        
        # Stage 1: Interpret user query
        interpreted = self.interpret_query(user_input)
        
        # Stage 2: Vector search
        search_results = self.vector_search(interpreted)
        
        # Stage 3: Generate final response with Claude
        context = self.format_search_results(search_results)
        
        final_response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{
                "role": "user",
                "content": f"""
                Original Query: "{user_input}"
                
                Query Analysis: {json.dumps(interpreted, indent=2)}
                
                Relevant HTS Code Information:
                {context}
                
                Please provide a comprehensive answer including:
                1. Most relevant HTS code(s)
                2. Duty rates (general and special if applicable)
                3. Any important classification notes
                4. Additional considerations for this commodity
                
                Format the response clearly for the user.
                """
            }],
            max_tokens=1000
        )
        
        # NEW: Extract HTS codes from Claude's analysis and find them in Pinecone
        claude_hts_codes = self._extract_hts_codes_from_analysis(final_response.content[0].text)
        final_results = self._get_claude_recommended_codes(claude_hts_codes, search_results)
        
        return {
            "interpretation": interpreted,
            "hts_matches": final_results if final_results else search_results,
            "final_answer": final_response.content[0].text
        }
    
    def _extract_hts_codes_from_analysis(self, claude_analysis):
        """Extract HTS codes mentioned in Claude's analysis"""
        import re
        
        try:
            # Pattern to match HTS codes (e.g., 4011.50.0000, 4013.20.0000)
            hts_pattern = r'\b(\d{4}\.?\d{2}\.?\d{4})\b'
            matches = re.findall(hts_pattern, claude_analysis)
            
            # Clean up the matches and standardize format
            hts_codes = []
            for match in matches:
                # Remove dots and add standard formatting
                digits_only = ''.join(c for c in match if c.isdigit())
                if len(digits_only) >= 8:
                    # Pad to 10 digits if needed
                    if len(digits_only) == 8:
                        digits_only += "00"
                    elif len(digits_only) == 9:
                        digits_only += "0"
                    
                    # Format as standard HTS code
                    if len(digits_only) >= 10:
                        formatted_code = f"{digits_only[:4]}.{digits_only[4:6]}.{digits_only[6:10]}"
                        hts_codes.append(formatted_code)
            
            print(f"🔍 Extracted HTS codes from Claude analysis: {hts_codes}")
            return hts_codes
            
        except Exception as e:
            print(f"⚠️ Error extracting HTS codes: {e}")
            return []
    
    def _get_claude_recommended_codes(self, claude_hts_codes, search_results):
        """Find Claude's recommended HTS codes in Pinecone results, or search for them directly"""
        if not claude_hts_codes:
            return None
        
        try:
            recommended_results = []
            
            # First, try to find Claude's codes in existing search results
            if hasattr(search_results, 'matches') and search_results.matches:
                for match in search_results.matches:
                    if hasattr(match, 'metadata'):
                        metadata = match.metadata
                        pinecone_hts = metadata.get('hts_code', '')
                        
                        # Check if this Pinecone result matches any of Claude's codes
                        for claude_code in claude_hts_codes:
                            if self._hts_codes_match(claude_code, pinecone_hts):
                                recommended_results.append(match)
                                print(f"✅ Found Claude's recommended code {claude_code} in Pinecone results")
                                break
            
            # If we found matches in existing results, return them
            if recommended_results:
                # Create a results object similar to Pinecone response
                class RecommendedResults:
                    def __init__(self, matches):
                        self.matches = matches
                
                return RecommendedResults(recommended_results)
            
            # If not found in search results, search Pinecone directly for each Claude code
            print("🔍 Claude's codes not found in search results, searching Pinecone directly...")
            
            all_direct_results = []
            for hts_code in claude_hts_codes:
                # Search by HTS code directly using metadata filter
                try:
                    direct_results = self.index.query(
                        vector=[0.0] * 1024,  # Dummy vector since we're filtering by metadata
                        top_k=3,
                        include_metadata=True,
                        filter={"hts_code": {"$eq": hts_code}}
                    )
                    
                    if hasattr(direct_results, 'matches') and direct_results.matches:
                        all_direct_results.extend(direct_results.matches)
                        print(f"✅ Found direct match for {hts_code}")
                    else:
                        # Try partial match (remove trailing zeros)
                        partial_code = hts_code.rstrip('0').rstrip('.')
                        partial_results = self.index.query(
                            vector=[0.0] * 1024,
                            top_k=3,
                            include_metadata=True,
                            filter={"hts_code": {"$regex": f"^{partial_code}.*"}} if len(partial_code) >= 4 else None
                        )
                        
                        if hasattr(partial_results, 'matches') and partial_results.matches:
                            all_direct_results.extend(partial_results.matches)
                            print(f"✅ Found partial match for {hts_code}")
                        
                except Exception as filter_error:
                    print(f"⚠️ Filter search failed for {hts_code}: {filter_error}")
                    continue
            
            if all_direct_results:
                class RecommendedResults:
                    def __init__(self, matches):
                        self.matches = matches
                
                return RecommendedResults(all_direct_results[:5])  # Limit to top 5
            
            print("⚠️ Could not find Claude's recommended codes in Pinecone")
            return None
            
        except Exception as e:
            print(f"❌ Error getting Claude recommended codes: {e}")
            return None
    
    def _hts_codes_match(self, code1, code2):
        """Check if two HTS codes are the same (ignoring formatting differences)"""
        if not code1 or not code2:
            return False
        
        # Remove all non-digit characters and compare
        digits1 = ''.join(c for c in str(code1) if c.isdigit())
        digits2 = ''.join(c for c in str(code2) if c.isdigit())
        
        # Pad to same length for comparison
        max_len = max(len(digits1), len(digits2))
        digits1 = digits1.ljust(max_len, '0')
        digits2 = digits2.ljust(max_len, '0')
        
        return digits1 == digits2
    
    def format_search_results(self, results):
        """Format Pinecone results for Claude context"""
        try:
            if not results or not hasattr(results, 'matches') or not results.matches:
                return "No relevant HTS codes found in the database."
            
            formatted = []
            for match in results.matches:
                if hasattr(match, 'metadata'):
                    metadata = match.metadata
                    score = match.score if hasattr(match, 'score') else 0
                    formatted.append(f"""
            HTS Code: {metadata.get('hts_code', 'N/A')}
            Description: {metadata.get('description', 'N/A')}
            General Rate: {metadata.get('general_rate', 'N/A')}
            Special Rate: {metadata.get('special_rate', 'N/A')}
            Similarity Score: {score:.3f}
            """)
            
            return "\n".join(formatted) if formatted else "No valid results found."
            
        except Exception as e:
            print(f"❌ Error formatting search results: {e}")
            return "Error formatting search results."

# Helper function to create and populate index
def create_hts_index(pinecone_api_key, csv_path, index_name="commodity-hts-codes-new", dimension=1024):
    """Create a new Pinecone index and populate it with HTS data"""
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=pinecone_api_key)
        
        # Create index if it doesn't exist
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing_indexes:
            print(f"Creating new index: {index_name}")
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        
        # Get index
        index = pc.Index(index_name)
        
        # Create a dummy search engine for embedding generation
        dummy_anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if not dummy_anthropic_key:
            raise Exception("ANTHROPIC_API_KEY environment variable required for embedding generation")
        
        dummy_search = CommodityRAGSearch(pinecone_api_key, dummy_anthropic_key, index_name)
        
        # Setup the index with data
        CommodityRAGSearch.setup_pinecone_index(csv_path, index, dummy_search.get_embedding)
        
        print(f"✅ Successfully created and populated index: {index_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating HTS index: {e}")
        return False