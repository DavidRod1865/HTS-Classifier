import pandas as pd
import numpy as np
from anthropic import Anthropic
import json
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from pathlib import Path

class LocalRAGSearch:
    def __init__(self, anthropic_api_key, csv_path="../../data/hts_2025_revision_13.csv"):
        """Initialize the Local RAG Search system"""
        self.anthropic = Anthropic(api_key=anthropic_api_key)
        self.csv_path = csv_path
        self.df = None
        self.embeddings = None
        self.model = None
        
        # Cache files
        self.embeddings_cache = "hts_embeddings.pkl"
        self.df_cache = "hts_dataframe.pkl"
        
        self.initialize()
    
    def initialize(self):
        """Initialize embeddings model and load/create HTS data"""
        try:
            print("🔄 Initializing sentence transformer model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, good quality embeddings
            print("✅ Sentence transformer model loaded")
            
            # Load or create embeddings
            if self._load_cached_data():
                print("✅ Loaded cached HTS data and embeddings")
            else:
                print("🔄 Creating embeddings from CSV data...")
                self._create_embeddings()
                print("✅ Embeddings created and cached")
                
        except Exception as e:
            print(f"❌ Error initializing Local RAG: {e}")
            raise e
    
    def _load_cached_data(self):
        """Load cached dataframe and embeddings if they exist"""
        try:
            if Path(self.embeddings_cache).exists() and Path(self.df_cache).exists():
                with open(self.embeddings_cache, 'rb') as f:
                    self.embeddings = pickle.load(f)
                
                with open(self.df_cache, 'rb') as f:
                    self.df = pickle.load(f)
                
                print(f"Loaded {len(self.df)} HTS codes with {self.embeddings.shape[1]}D embeddings")
                return True
            return False
        except Exception as e:
            print(f"⚠️ Error loading cached data: {e}")
            return False
    
    def _create_embeddings(self):
        """Create embeddings from CSV data"""
        # Load CSV
        full_path = os.path.join(os.path.dirname(__file__), self.csv_path)
        df = pd.read_csv(full_path, low_memory=False)
        
        # Filter to leaf nodes only (actual HTS codes)
        self.df = df[df['Is Leaf Node'] == 'Yes'].copy().reset_index(drop=True)
        
        # Create comprehensive text for each HTS code
        texts = []
        for _, row in self.df.iterrows():
            text_parts = []
            
            # Add description
            if pd.notna(row['Enhanced Description']):
                text_parts.append(str(row['Enhanced Description']))
            
            # Add context path
            if pd.notna(row['Context Path']):
                text_parts.append(str(row['Context Path']))
            
            # Add search keywords
            if pd.notna(row['Search Keywords']):
                text_parts.append(str(row['Search Keywords']))
            
            # Combine all text
            combined_text = " | ".join(text_parts) if text_parts else "No description available"
            texts.append(combined_text)
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} HTS codes...")
        self.embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Cache the results
        with open(self.embeddings_cache, 'wb') as f:
            pickle.dump(self.embeddings, f)
        
        with open(self.df_cache, 'wb') as f:
            pickle.dump(self.df, f)
        
        print(f"✅ Created embeddings: {self.embeddings.shape}")
    
    def interpret_query(self, user_input):
        """Stage 1: Have Claude understand and structure the query"""
        
        prompt = f"""
        Analyze this commodity/product search query and extract structured information for HTS classification:
        
        User Query: "{user_input}"
        
        Please provide a JSON response with:
        1. "commodity_type" - main product category (e.g., textiles, metals, electronics, food, chemicals)
        2. "specific_product" - exact item if mentioned 
        3. "key_attributes" - important characteristics (material, use, size, etc.)
        4. "search_intent" - what user wants (classification, duty rates, regulations, etc.)
        5. "optimized_query" - enhanced search query for better HTS matching
        
        Examples:
        - "cotton t-shirts from China" → commodity_type: "textiles", specific_product: "cotton t-shirts", key_attributes: ["cotton", "apparel", "knitted"], optimized_query: "cotton knitted shirts textile apparel clothing"
        - "steel pipes for construction" → commodity_type: "metals", specific_product: "steel pipes", key_attributes: ["steel", "tubes", "construction"], optimized_query: "steel tubes pipes metal construction materials"
        
        Focus on terms that would appear in official HTS descriptions and trade documentation.
        Return only valid JSON.
        """
        
        try:
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            
            return json.loads(response.content[0].text)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing failed for query interpretation: {e}")
            return self._fallback_interpretation(user_input)
        except Exception as e:
            print(f"⚠️ Error in interpret_query: {e}")
            return self._fallback_interpretation(user_input)
    
    def _fallback_interpretation(self, user_input):
        """Fallback interpretation if Claude fails"""
        return {
            "commodity_type": "general",
            "specific_product": user_input,
            "key_attributes": [user_input],
            "search_intent": "classification",
            "optimized_query": user_input
        }
    
    def vector_search(self, interpreted_query, top_k=10):
        """Stage 2: Perform vector search on HTS embeddings"""
        
        try:
            if self.embeddings is None or self.df is None:
                raise Exception("Embeddings not initialized")
            
            # Use the optimized query for search
            search_text = interpreted_query.get('optimized_query', interpreted_query.get('specific_product', ''))
            
            if not search_text.strip():
                print("⚠️ Warning: Empty search text")
                return []
            
            # Generate query embedding
            query_embedding = self.model.encode([search_text])
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # Get top matches
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                similarity_score = similarities[idx]
                if similarity_score > 0.1:  # Minimum similarity threshold
                    row = self.df.iloc[idx]
                    results.append({
                        'similarity': float(similarity_score),
                        'hts_data': row.to_dict(),
                        'index': int(idx)
                    })
            
            return results
            
        except Exception as e:
            print(f"❌ Error in vector_search: {e}")
            return []
    
    def synthesize_results(self, user_query, interpreted_query, search_results):
        """Stage 3: Have Claude synthesize the final response"""
        
        if not search_results:
            return "No relevant HTS classifications found for this query. Try being more specific about the product material, intended use, or other distinguishing characteristics."
        
        # Format search results for Claude
        context_parts = []
        for i, result in enumerate(search_results[:5], 1):
            hts_data = result['hts_data']
            similarity = result['similarity']
            
            context_parts.append(f"""
            Match #{i} (Similarity: {similarity:.3f}):
            - HTS Code: {hts_data.get('HTS Number', 'N/A')}
            - Description: {hts_data.get('Enhanced Description', 'N/A')}
            - Context: {hts_data.get('Context Path', 'N/A')}
            - General Duty: {hts_data.get('General Rate of Duty', 'N/A')}
            - Special Duty: {hts_data.get('Special Rate of Duty', 'N/A')}
            - Unit: {hts_data.get('Unit of Quantity', 'N/A')}
            """)
        
        context = "\n".join(context_parts)
        
        prompt = f"""
        Original User Query: "{user_query}"
        
        Query Analysis: {json.dumps(interpreted_query, indent=2)}
        
        Most Relevant HTS Classifications:
        {context}
        
        Based on the user's query and the HTS classification matches above, please provide a comprehensive response that includes:
        
        1. **Primary HTS Classification**: The most appropriate HTS code(s) for this product
        2. **Duty Information**: Current duty rates (general and special if applicable)
        3. **Classification Rationale**: Brief explanation of why this classification applies
        4. **Important Notes**: Any special requirements, exclusions, or considerations
        5. **Alternative Classifications**: If applicable, mention other possible codes
        
        Format your response to be practical and actionable for someone importing/exporting this product.
        Focus on the most relevant results and provide clear guidance.
        """
        
        try:
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            
            return response.content[0].text
        except Exception as e:
            print(f"⚠️ Error generating synthesis: {e}")
            return f"Found {len(search_results)} potential HTS classifications. Please review the search results for the most appropriate classification."
    
    def search(self, user_input):
        """Complete RAG search pipeline"""
        try:
            # Stage 1: Interpret user query with Claude
            print(f"🔍 Stage 1: Interpreting query: {user_input}")
            interpreted_query = self.interpret_query(user_input)
            
            # Stage 2: Vector search for relevant HTS codes
            print(f"🔍 Stage 2: Vector search with: {interpreted_query.get('optimized_query', user_input)}")
            search_results = self.vector_search(interpreted_query)
            
            # Stage 3: Synthesize results with Claude
            print(f"🔍 Stage 3: Synthesizing {len(search_results)} results")
            final_answer = self.synthesize_results(user_input, interpreted_query, search_results)
            
            # Format results for frontend
            formatted_results = []
            for result in search_results[:10]:
                hts_data = result['hts_data']
                hts_code = str(hts_data.get('HTS Number', ''))
                
                # Format HTS code
                if hts_code and len(hts_code) >= 10:
                    formatted_code = f"{hts_code[:4]}.{hts_code[4:6]}.{hts_code[6:10]}"
                else:
                    formatted_code = hts_code
                
                formatted_results.append({
                    "hts_code": formatted_code,
                    "description": str(hts_data.get('Enhanced Description', '')),
                    "effective_duty": str(hts_data.get('General Rate of Duty', 'Free')),
                    "confidence_score": int(result['similarity'] * 100),
                    "match_type": "rag_search",
                    "chapter": formatted_code[:2] if formatted_code else '',
                    "unit": str(hts_data.get('Unit of Quantity', '')),
                    "special_duty": str(hts_data.get('Special Rate of Duty', '')),
                    "duty_source": "usitc",
                    "context_path": str(hts_data.get('Context Path', ''))
                })
            
            return {
                "interpretation": interpreted_query,
                "hts_matches": formatted_results,
                "final_answer": final_answer,
                "search_method": "local_rag"
            }
            
        except Exception as e:
            print(f"❌ Error in RAG search: {e}")
            return {
                "interpretation": {"error": str(e)},
                "hts_matches": [],
                "final_answer": f"Error during search: {str(e)}",
                "search_method": "local_rag"
            }