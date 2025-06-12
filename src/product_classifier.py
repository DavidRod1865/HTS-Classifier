"""
Product Classifier Module

This module handles product confirmation and classification logic,
including creating final classification results and managing options.
"""

from typing import List, Dict, Optional
from anthropic import Anthropic
from constants import *
from csv_hts_loader import CSVHTSLoader


class ProductClassifier:
    """
    Handles product classification and result formatting.
    """
    
    def __init__(
        self, 
        hts_loader: CSVHTSLoader, 
        claude_client: Optional[Anthropic] = None, 
        claude_model: str = None
    ):
        """Initialize the product classifier."""
        self.hts_loader = hts_loader
        self.claude_client = claude_client
        self.claude_model = claude_model
    
    def confirm_product_understanding(self, user_input: str) -> str:
        """Use Claude to confirm understanding of what user wants to import."""
        if self.claude_client:
            return self._claude_confirm_product(user_input)
        else:
            # Fallback: use input as-is
            return user_input.strip()
    
    def create_final_classification(
        self, 
        candidates: List[Dict], 
        current_turn: int
    ) -> Optional[Dict]:
        """Create final classification based on candidates and conversation state."""
        if not candidates:
            return None
        
        # Get high confidence candidates
        high_confidence = [c for c in candidates if c.get('confidence_score', 0) >= HIGH_CONFIDENCE_THRESHOLD]
        
        if len(high_confidence) >= 1:
            # Present high confidence results for selection
            return self._create_options_classification(
                high_confidence[:MAX_DISPLAY_OPTIONS], 
                CLASSIFICATION_TYPES['HIGH_CONFIDENCE_OPTIONS'],
                "I found high-confidence HTS classification options. Please review and select the one that best matches your product:"
            )
        
        elif current_turn > MAX_CONVERSATION_TURNS:
            # Reached question limit - present top options
            return self._create_options_classification(
                candidates[:3], 
                CLASSIFICATION_TYPES['FINAL_OPTIONS'],
                f"After {MAX_CONVERSATION_TURNS} questions, here are the best HTS classification options. Please select the one that best describes your product:"
            )
        
        else:
            # Single best candidate
            best_candidate = candidates[0]
            return self._create_single_classification(best_candidate)
    
    def create_user_selection_result(self, selected_option: Dict) -> Dict:
        """Create final classification from user selection."""
        return {
            "type": CLASSIFICATION_TYPES['USER_SELECTED'],
            "hts_code": selected_option['hts_code'],
            "description": selected_option['description'],
            "confidence_score": selected_option['confidence_score'],
            "effective_duty": selected_option['effective_duty'],
            "full_details": selected_option['full_details'],
            "classification_reasoning": f"User selected from options"
        }
    
    def create_invalid_selection_response(self, options: List[Dict]) -> Dict:
        """Create response for invalid user selection."""
        return {
            "message": f"Please select a valid option (1-{len(options)}) or provide the HTS code:",
            "invalid_selection": True
        }
    
    def _claude_confirm_product(self, user_input: str) -> str:
        """Use Claude to confirm understanding of what user wants to import."""
        try:
            prompt = f"""You are an experienced U.S. Customs Broker helping classify products for import.

A client said they want to import: "{user_input}"

As a customs broker, briefly confirm your understanding of what product they want to import. Be specific and clear about the product type, but keep it concise (1-2 sentences max).

Examples:
- Input: "tires" → Output: "New pneumatic rubber tires for motor vehicles"
- Input: "laptop computer" → Output: "Portable automatic data processing machines (laptop computers)"
- Input: "wooden chairs" → Output: "Wooden furniture seating (chairs)"
- Input: "pastry" → Output: "Baked pastry products and confectionery items"

Your confirmation:"""

            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            
            confirmed = response.content[0].text.strip()
            return confirmed if confirmed else user_input.strip()
            
        except Exception as e:
            print(ERROR_MESSAGES['claude_error'].format('confirmation', e))
            return user_input.strip()
    
    def _create_options_classification(
        self, 
        candidates: List[Dict], 
        classification_type: str, 
        message: str
    ) -> Dict:
        """Create classification with multiple options for user selection."""
        classification_options = []
        
        for i, candidate in enumerate(candidates):
            hts_code = candidate['hts_code']
            full_details = self.hts_loader.lookup_with_effective_rate(hts_code)
            
            classification_options.append({
                "index": i + 1,
                "hts_code": hts_code,
                "description": candidate['description'],
                "confidence_score": candidate['confidence_score'],
                "effective_duty": candidate['effective_duty'],
                "full_details": full_details,
                "match_type": candidate.get('match_type', 'unknown')
            })
        
        return {
            "type": classification_type,
            "options": classification_options,
            "message": message,
            "selection_needed": True
        }
    
    def _create_single_classification(self, candidate: Dict) -> Dict:
        """Create single classification result."""
        hts_code = candidate['hts_code']
        full_details = self.hts_loader.lookup_with_effective_rate(hts_code)
        
        return {
            "type": CLASSIFICATION_TYPES['SINGLE_CLASSIFICATION'],
            "hts_code": hts_code,
            "description": candidate['description'],
            "confidence_score": candidate['confidence_score'],
            "effective_duty": candidate['effective_duty'],
            "full_details": full_details,
            "classification_reasoning": f"Best match with {candidate['confidence_score']}% confidence"
        }