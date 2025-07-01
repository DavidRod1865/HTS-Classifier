import pandas as pd
import os
from fuzzywuzzy import fuzz
from anthropic import Anthropic
import json
import re

class SimpleHTSSearch:
    def __init__(self, anthropic_api_key, csv_path="../../data/hts_2025_revision_13.csv"):
        """Initialize with CSV data loaded into memory"""
        self.anthropic = Anthropic(api_key=anthropic_api_key)
        self.csv_path = csv_path
        self.df = None
        self.load_csv_data()
    
    def load_csv_data(self):
        """Load and prepare CSV data for searching"""
        try:
            full_path = os.path.join(os.path.dirname(__file__), self.csv_path)
            self.df = pd.read_csv(full_path, low_memory=False)
            
            # Filter to only leaf nodes (actual HTS codes)
            self.df = self.df[self.df['Is Leaf Node'] == 'Yes'].copy()
            
            # Clean up data
            self.df['Enhanced Description'] = self.df['Enhanced Description'].fillna('')
            self.df['Search Keywords'] = self.df['Search Keywords'].fillna('')
            self.df['Context Path'] = self.df['Context Path'].fillna('')
            
            # Create combined search text for each row
            self.df['search_text'] = (
                self.df['Enhanced Description'].astype(str) + ' ' +
                self.df['Search Keywords'].astype(str) + ' ' + 
                self.df['Context Path'].astype(str)
            ).str.lower()
            
            print(f"✅ Loaded {len(self.df)} HTS codes for searching")
            
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            self.df = pd.DataFrame()
    
    def search_hts_codes(self, query, max_results=10):
        """Search HTS codes using fuzzy matching and keyword search"""
        if self.df is None or self.df.empty:
            return []
        
        query_lower = query.lower()
        results = []
        
        # Method 1: Exact keyword matches
        exact_matches = self.df[
            self.df['search_text'].str.contains(query_lower, na=False, regex=False)
        ].copy()
        
        # Method 2: Fuzzy matching on descriptions
        fuzzy_scores = []
        for idx, row in self.df.iterrows():
            description = str(row['Enhanced Description']).lower()
            keywords = str(row['Search Keywords']).lower()
            
            # Calculate fuzzy match scores
            desc_score = fuzz.partial_ratio(query_lower, description)
            keyword_score = fuzz.partial_ratio(query_lower, keywords)
            max_score = max(desc_score, keyword_score)
            
            if max_score > 60:  # Minimum threshold
                fuzzy_scores.append({
                    'index': idx,
                    'score': max_score,
                    'row': row
                })
        
        # Sort by score and combine results
        fuzzy_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Add exact matches first
        for _, row in exact_matches.head(max_results//2).iterrows():
            results.append(self._format_hts_result(row, 95))
        
        # Add fuzzy matches
        remaining_slots = max_results - len(results)
        for item in fuzzy_scores[:remaining_slots]:
            if item['index'] not in exact_matches.index:
                results.append(self._format_hts_result(item['row'], item['score']))
        
        return results[:max_results]
    
    def _format_hts_result(self, row, confidence_score):
        """Format a single HTS result"""
        hts_code = str(row['HTS Number']) if pd.notna(row['HTS Number']) else ''
        
        # Format HTS code to standard format
        if hts_code and len(hts_code) >= 10:
            formatted_code = f"{hts_code[:4]}.{hts_code[4:6]}.{hts_code[6:10]}"
        else:
            formatted_code = hts_code
        
        return {
            "hts_code": formatted_code,
            "description": str(row['Enhanced Description']) if pd.notna(row['Enhanced Description']) else '',
            "effective_duty": str(row['General Rate of Duty']) if pd.notna(row['General Rate of Duty']) else 'Free',
            "confidence_score": int(confidence_score),
            "match_type": "csv_search",
            "chapter": formatted_code[:2] if formatted_code else '',
            "unit": str(row['Unit of Quantity']) if pd.notna(row['Unit of Quantity']) else '',
            "special_duty": str(row['Special Rate of Duty']) if pd.notna(row['Special Rate of Duty']) else '',
            "duty_source": "usitc",
            "context_path": str(row['Context Path']) if pd.notna(row['Context Path']) else ''
        }
    
    def interpret_and_search(self, user_query):
        """Complete search pipeline with Claude interpretation"""
        
        # Step 1: Have Claude interpret the query
        interpretation = self._interpret_query(user_query)
        
        # Step 2: Search using multiple strategies
        search_terms = self._extract_search_terms(interpretation, user_query)
        all_results = []
        
        # Search with each term and combine results
        for term in search_terms:
            results = self.search_hts_codes(term, max_results=5)
            all_results.extend(results)
        
        # Remove duplicates based on HTS code
        seen_codes = set()
        unique_results = []
        for result in all_results:
            if result['hts_code'] not in seen_codes:
                seen_codes.add(result['hts_code'])
                unique_results.append(result)
        
        # Sort by confidence score
        unique_results.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        # Step 3: Have Claude analyze and provide final answer
        final_analysis = self._generate_final_analysis(user_query, unique_results[:10])
        
        return {
            "interpretation": interpretation,
            "hts_matches": unique_results[:10],
            "final_answer": final_analysis,
            "search_terms": search_terms
        }
    
    def _interpret_query(self, user_input):
        """Have Claude interpret the user query"""
        prompt = f"""
        Analyze this product search query and extract structured information:
        
        User Query: "{user_input}"
        
        Please provide a JSON response with:
        1. "commodity_type" - main product category
        2. "specific_product" - exact item if mentioned
        3. "search_terms" - 3-5 optimized search terms for HTS lookup
        4. "intent" - what the user wants (classification, rates, etc.)
        
        Focus on terms that would appear in HTS descriptions and trade documents.
        Return only valid JSON.
        """
        
        try:
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            
            return json.loads(response.content[0].text)
        except Exception as e:
            print(f"⚠️ Error in query interpretation: {e}")
            return {
                "commodity_type": "general",
                "specific_product": user_input,
                "search_terms": [user_input],
                "intent": "classification"
            }
    
    def _extract_search_terms(self, interpretation, original_query):
        """Extract search terms from interpretation and original query"""
        terms = [original_query]
        
        if interpretation.get('search_terms'):
            terms.extend(interpretation['search_terms'])
        
        if interpretation.get('specific_product'):
            terms.append(interpretation['specific_product'])
        
        if interpretation.get('commodity_type'):
            terms.append(interpretation['commodity_type'])
        
        # Remove duplicates and empty terms
        unique_terms = list(set([term.strip() for term in terms if term and term.strip()]))
        return unique_terms[:5]  # Limit to 5 terms
    
    def _generate_final_analysis(self, user_query, results):
        """Generate final analysis with Claude"""
        if not results:
            return "No HTS classifications found for this query. Try being more specific about the product material, use, or characteristics."
        
        results_text = "\n".join([
            f"HTS {r['hts_code']}: {r['description']} (Duty: {r['effective_duty']}, Confidence: {r['confidence_score']}%)"
            for r in results[:5]
        ])
        
        prompt = f"""
        Original Query: "{user_query}"
        
        Found HTS Classifications:
        {results_text}
        
        Please provide a comprehensive analysis including:
        1. The most relevant HTS code(s) for this product
        2. Key duty rates and any special considerations
        3. Brief explanation of why these classifications apply
        4. Any important notes about classification requirements
        
        Keep the response concise and practical for import/export purposes.
        """
        
        try:
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800
            )
            
            return response.content[0].text
        except Exception as e:
            print(f"⚠️ Error generating final analysis: {e}")
            return f"Found {len(results)} potential HTS classifications. Review the results above for the most appropriate classification."