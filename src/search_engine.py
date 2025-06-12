"""
HTS Search Engine Module

This module handles all HTS code search functionality including:
- Comprehensive search strategies
- Relevance scoring
- Product-specific matching
- Chapter-based targeting
"""

from typing import List, Dict, Set, Tuple, Optional
import pandas as pd
from constants import *
from csv_hts_loader import CSVHTSLoader


class HTSSearchEngine:
    """
    Handles all HTS search operations with multiple search strategies
    and intelligent relevance scoring.
    """
    
    def __init__(self, hts_loader: CSVHTSLoader):
        """Initialize the search engine with an HTS loader."""
        self.hts_loader = hts_loader
    
    def comprehensive_search(self, product_description: str) -> List[Dict]:
        """
        Perform comprehensive search for HTS codes using multiple strategies.
        Returns only complete HTS codes with duty rates.
        """
        all_results = []
        seen_codes = set()
        
        print(f"🔍 Comprehensive search for: '{product_description}'")
        
        # Step 1: Direct text search
        exact_matches = self._exact_text_search(product_description, seen_codes)
        all_results.extend(exact_matches)
        
        # Step 2: Fuzzy search
        fuzzy_matches = self._fuzzy_search(product_description, seen_codes)
        all_results.extend(fuzzy_matches)
        
        # Step 3: Enhanced semantic search if needed
        if len(all_results) < 3:
            semantic_results = self._enhanced_semantic_search(product_description, seen_codes)
            all_results.extend(semantic_results)
        
        # Sort by confidence and return top results
        all_results.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        print(f"   Final: {len(all_results)} complete HTS codes found")
        if all_results:
            print(f"   Top result: {all_results[0]['hts_code']} - {all_results[0]['description'][:60]}...")
        
        return all_results[:MAX_CLASSIFICATION_OPTIONS]
    
    def _exact_text_search(self, product_description: str, seen_codes: Set[str]) -> List[Dict]:
        """Perform exact text search and return complete HTS codes."""
        results = []
        exact_matches = self.hts_loader.search_simple(product_description, max_results=DEFAULT_MAX_SEARCH_RESULTS)
        print(f"   Found {len(exact_matches)} exact matches")
        
        for _, row in exact_matches.iterrows():
            if self._is_valid_result(row, seen_codes, product_description):
                duty_info = self.hts_loader.get_effective_duty_rate(row['HTS Number'])
                
                result = self._create_search_result(
                    row, duty_info, EXACT_MATCH_CONFIDENCE, 'exact_match'
                )
                results.append(result)
                seen_codes.add(row['HTS Number'])
        
        return results
    
    def _fuzzy_search(self, product_description: str, seen_codes: Set[str]) -> List[Dict]:
        """Perform fuzzy search and return complete HTS codes."""
        results = []
        fuzzy_matches = self.hts_loader.search_fuzzy(
            product_description, 
            max_results=DEFAULT_FUZZY_SEARCH_RESULTS, 
            min_score=DEFAULT_MIN_FUZZY_SCORE
        )
        print(f"   Found {len(fuzzy_matches)} fuzzy matches")
        
        for _, row in fuzzy_matches.iterrows():
            if self._is_valid_result(row, seen_codes, product_description):
                duty_info = self.hts_loader.get_effective_duty_rate(row['HTS Number'])
                confidence = min(FUZZY_MATCH_MAX_CONFIDENCE, max(FUZZY_MATCH_MIN_CONFIDENCE, row.get('Similarity_Score', 70)))
                
                result = self._create_search_result(
                    row, duty_info, confidence, 'fuzzy_match'
                )
                results.append(result)
                seen_codes.add(row['HTS Number'])
        
        return results
    
    def _enhanced_semantic_search(self, product_description: str, seen_codes: Set[str]) -> List[Dict]:
        """Enhanced semantic search when initial search yields few results."""
        results = []
        print(f"🧠 Enhanced semantic search for: '{product_description}'")
        
        # Extract key words and search
        key_words = self._extract_key_words(product_description)
        print(f"   Key words extracted: {key_words}")
        
        for word in key_words:
            if len(word) > 3:
                word_matches = self.hts_loader.search_simple(word, max_results=DEFAULT_CHAPTER_SEARCH_RESULTS)
                
                for _, row in word_matches.iterrows():
                    if self._is_valid_enhanced_result(row, seen_codes, product_description):
                        duty_info = self.hts_loader.get_effective_duty_rate(row['HTS Number'])
                        relevance_score = self._calculate_relevance_score(product_description, row['Description'])
                        
                        if relevance_score > LOW_CONFIDENCE_THRESHOLD:
                            result = self._create_search_result(
                                row, duty_info, min(SEMANTIC_SEARCH_MAX_CONFIDENCE, relevance_score), 'semantic_search'
                            )
                            results.append(result)
                            seen_codes.add(row['HTS Number'])
        
        # Chapter-targeted search as fallback
        if len(results) < 2:
            chapter_results = self._targeted_chapter_search(product_description, seen_codes)
            results.extend(chapter_results)
        
        results.sort(key=lambda x: x['confidence_score'], reverse=True)
        print(f"   Enhanced search found {len(results)} additional results")
        
        return results[:DEFAULT_ENHANCED_SEARCH_RESULTS]
    
    def _targeted_chapter_search(self, product_description: str, seen_codes: Set[str]) -> List[Dict]:
        """Search within the most relevant chapters."""
        results = []
        target_chapters = self._get_target_chapters(product_description)
        
        for chapter in target_chapters[:2]:  # Top 2 chapters
            chapter_data = self.hts_loader.get_chapter(chapter)
            detailed_items = chapter_data[
                (chapter_data['Indent'] >= MIN_DETAIL_INDENT_LEVEL) &
                (chapter_data['HTS Number'].str.len() >= MIN_COMPLETE_HTS_LENGTH)
            ]
            
            for _, row in detailed_items.head(3).iterrows():
                if row['HTS Number'] and row['HTS Number'] not in seen_codes:
                    duty_info = self.hts_loader.get_effective_duty_rate(row['HTS Number'])
                    result = self._create_search_result(
                        row, duty_info, CHAPTER_FALLBACK_CONFIDENCE, 'chapter_fallback'
                    )
                    results.append(result)
                    seen_codes.add(row['HTS Number'])
        
        return results
    
    def _is_valid_result(self, row, seen_codes: Set[str], product_description: str) -> bool:
        """Check if a search result is valid and relevant."""
        hts_number = row['HTS Number']
        return (
            hts_number and 
            hts_number not in seen_codes and
            self._is_complete_hts_code(hts_number) and
            self._is_relevant_for_product(product_description, row)
        )
    
    def _is_valid_enhanced_result(self, row, seen_codes: Set[str], product_description: str) -> bool:
        """Enhanced validation for semantic search results."""
        if not self._is_valid_result(row, seen_codes, product_description):
            return False
        
        # Additional checks for enhanced search
        indent = row.get('Indent', 0)
        return indent >= MIN_DETAIL_INDENT_LEVEL
    
    def _is_complete_hts_code(self, hts_code: str) -> bool:
        """Check if this is a complete HTS code."""
        if not hts_code or not isinstance(hts_code, str):
            return False
        
        clean_code = hts_code.replace('.', '').strip()
        
        return (
            len(clean_code) >= MIN_COMPLETE_HTS_LENGTH and
            len(clean_code) > MIN_HEADING_LENGTH and
            clean_code.isdigit()
        )
    
    def _is_relevant_for_product(self, product_description: str, row) -> bool:
        """Check if HTS row is relevant for the product."""
        try:
            product_lower = product_description.lower()
            desc_lower = str(row.get('Description', '')).lower()
            hts_number = str(row.get('HTS Number', ''))
            
            if not self._is_complete_hts_code(hts_number):
                return False
            
            if row.get('Indent', 0) < MIN_DETAIL_INDENT_LEVEL:
                return False
            
            # Check for term overlap
            product_terms = self._extract_terms(product_lower)
            desc_terms = self._extract_terms(desc_lower)
            
            # Direct overlap
            if product_terms.intersection(desc_terms):
                return True
            
            # Partial word matches
            for product_term in product_terms:
                if len(product_term) > 3:
                    for desc_term in desc_terms:
                        if product_term in desc_term or desc_term in product_term:
                            return True
            
            # Product-specific relevance
            return self._check_product_specific_relevance(product_lower, desc_lower)
            
        except Exception as e:
            print(ERROR_MESSAGES['relevance_check_error'].format(e))
            return False
    
    def _check_product_specific_relevance(self, product_input: str, description: str) -> bool:
        """Enhanced product-specific relevance checking."""
        # Check product synonyms
        for product, synonyms in PRODUCT_SYNONYMS.items():
            if product in product_input:
                if any(synonym in description for synonym in synonyms):
                    return True
        
        # Check material relevance
        for material, related_terms in MATERIAL_KEYWORDS.items():
            if material in product_input:
                if any(term in description for term in related_terms):
                    return True
        
        return False
    
    def _extract_terms(self, text: str) -> Set[str]:
        """Extract meaningful terms from text."""
        terms = set(text.split())
        return terms - COMMON_STOP_WORDS
    
    def _extract_key_words(self, product_description: str) -> List[str]:
        """Extract key words from product description for enhanced search."""
        words = product_description.lower().split()
        key_words = [word for word in words if word not in COMMON_STOP_WORDS and len(word) > 2]
        return key_words[:3]  # Return top 3 key words
    
    def _get_target_chapters(self, product_description: str) -> List[str]:
        """Get target chapters for product-specific search."""
        product_lower = product_description.lower()
        target_chapters = []
        
        for product_term, chapters in PRODUCT_CHAPTER_MAPPING.items():
            if product_term in product_lower:
                if isinstance(chapters, dict):
                    # Weighted chapters - sort by weight
                    sorted_chapters = sorted(chapters.items(), key=lambda x: x[1], reverse=True)
                    target_chapters.extend([ch for ch, _ in sorted_chapters])
                else:
                    # Simple list
                    target_chapters.extend(chapters)
        
        return list(dict.fromkeys(target_chapters))  # Remove duplicates while preserving order
    
    def _calculate_relevance_score(self, product_description: str, hts_description: str) -> int:
        """Calculate relevance score between product and HTS description."""
        product_words = self._extract_terms(product_description.lower())
        hts_words = self._extract_terms(hts_description.lower())
        
        if not product_words:
            return 0
        
        # Calculate exact matches
        exact_matches = product_words.intersection(hts_words)
        exact_score = (len(exact_matches) / len(product_words)) * EXACT_MATCH_SCORE_WEIGHT
        
        # Calculate partial matches
        partial_score = 0
        for prod_word in product_words:
            if len(prod_word) > 3:
                for hts_word in hts_words:
                    if prod_word in hts_word or hts_word in prod_word:
                        partial_score += PARTIAL_MATCH_SCORE_WEIGHT
                        break
        
        return int(exact_score + min(partial_score, MAX_PARTIAL_MATCH_BONUS))
    
    def _create_search_result(self, row, duty_info: Dict, confidence: float, match_type: str) -> Dict:
        """Create a standardized search result."""
        return {
            "hts_code": row['HTS Number'],
            "description": row['Description'],
            "confidence_score": confidence,
            "match_type": match_type,
            "effective_duty": duty_info.get('effective_rate', 'Unknown'),
            "chapter": row['HTS Number'][:2] if len(row['HTS Number']) >= 2 else '',
            "indent": row['Indent'],
            "full_details": duty_info,
            "usitc_link": f"https://hts.usitc.gov/search?query={row['HTS Number']}"
        }