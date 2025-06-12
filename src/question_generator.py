"""
Question Generator Module

This module handles generating intelligent clarifying questions
for HTS classification based on search results and conversation context.
"""

from typing import List, Dict, Optional
import json
from anthropic import Anthropic
from constants import *


class QuestionGenerator:
    """
    Generates intelligent clarifying questions to improve HTS classification accuracy.
    """
    
    def __init__(self, claude_client: Optional[Anthropic] = None, claude_model: str = None):
        """Initialize the question generator."""
        self.claude_client = claude_client
        self.claude_model = claude_model
    
    def generate_questions(
        self, 
        confirmed_product: str, 
        candidates: List[Dict], 
        conversation_history: List[Dict], 
        current_turn: int
    ) -> List[str]:
        """
        Generate exactly 3 clarifying questions for the current turn.
        """
        print(f"🔍 Generating clarifying questions for turn {current_turn}...")
        
        # Enforce turn limit
        if current_turn > MAX_CONVERSATION_TURNS:
            print(f"   ⏰ {MAX_CONVERSATION_TURNS}-question limit reached - no more questions")
            return []
        
        # Generate questions using Claude or fallback
        if self.claude_client:
            questions = self._claude_generate_questions(
                confirmed_product, candidates, conversation_history, current_turn
            )
        else:
            questions = self._fallback_generate_questions(confirmed_product, candidates, current_turn)
        
        print(f"   Generated {len(questions)} questions for turn {current_turn}")
        return questions
    
    def _claude_generate_questions(
        self, 
        confirmed_product: str, 
        candidates: List[Dict], 
        conversation_history: List[Dict], 
        current_turn: int
    ) -> List[str]:
        """Use Claude to generate exactly 3 clarifying questions."""
        try:
            context = self._prepare_context_for_questions(candidates, conversation_history)
            prompt = self._build_question_prompt(
                confirmed_product, context, conversation_history, current_turn
            )
            
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            questions_text = response.content[0].text.strip()
            questions = [
                q.strip() for q in questions_text.split('\n') 
                if q.strip() and len(q.strip()) > MIN_QUESTION_LENGTH
            ]
            
            # Ensure exactly 3 questions
            while len(questions) < MAX_CLARIFYING_QUESTIONS:
                questions.extend(
                    self._fallback_generate_questions(confirmed_product, candidates, current_turn)
                )
            
            return questions[:MAX_CLARIFYING_QUESTIONS]
            
        except Exception as e:
            print(ERROR_MESSAGES['claude_error'].format('question generation', e))
            return self._fallback_generate_questions(confirmed_product, candidates, current_turn)
    
    def _build_question_prompt(
        self, 
        confirmed_product: str, 
        context: str, 
        conversation_history: List[Dict], 
        current_turn: int
    ) -> str:
        """Build the prompt for Claude question generation."""
        return f"""You are an experienced U.S. Customs Broker with 20+ years of experience. You're helping classify this product for import: "{confirmed_product}"

CURRENT SITUATION:
- Turn: {current_turn} of {MAX_CONVERSATION_TURNS} maximum
- Previous conversation: {json.dumps(conversation_history, indent=2)}

POTENTIAL HTS MATCHES:
{context}

YOUR TASK:
Generate exactly {MAX_CLARIFYING_QUESTIONS} separate clarifying questions to help determine the correct HTS classification. Each question should:
- Be a complete, standalone question
- Help distinguish between the potential matches
- Be something an importer would know about their product
- Be professionally worded as a customs broker would ask

QUESTION FOCUS FOR TURN {current_turn}:
{QUESTION_FOCUS.get(current_turn, 'Ask clarifying questions to narrow down classification')}

FORMAT: Return exactly {MAX_CLARIFYING_QUESTIONS} questions, each on its own line, no numbering or bullets.

EXAMPLE:
What is the primary material composition of your tires?
Are these tires intended for passenger vehicles or commercial trucks?
What is the tire size and load capacity specification?"""
    
    def _fallback_generate_questions(
        self, 
        product: str, 
        candidates: List[Dict], 
        turn: int
    ) -> List[str]:
        """Generate fallback questions when Claude isn't available."""
        return FALLBACK_QUESTIONS.get(turn, FALLBACK_QUESTIONS[3])
    
    def _prepare_context_for_questions(
        self, 
        candidates: List[Dict], 
        conversation_history: List[Dict]
    ) -> str:
        """Prepare context for question generation."""
        if not candidates:
            return "No specific matches found yet."
        
        context_lines = []
        for candidate in candidates[:MAX_DISPLAY_OPTIONS]:  # Top 5
            confidence = candidate.get('confidence_score', 0)
            duty = candidate.get('effective_duty', 'Unknown')
            context_lines.append(
                f"• {candidate['hts_code']} ({confidence}%): {candidate['description'][:80]}..."
            )
            context_lines.append(f"  Duty: {duty}")
        
        return '\n'.join(context_lines)


class ResponseMatcher:
    """
    Handles matching user responses to available options using Claude AI.
    """
    
    def __init__(self, claude_client: Optional[Anthropic] = None, claude_model: str = None):
        """Initialize the response matcher."""
        self.claude_client = claude_client
        self.claude_model = claude_model
    
    def match_user_selection(self, user_input: str, options: List[Dict]) -> Optional[Dict]:
        """Match user's response to one of the available options."""
        # Try simple numeric selection first
        selected_option = self._try_numeric_selection(user_input, options)
        if selected_option:
            return selected_option
        
        # Try HTS code matching
        selected_option = self._try_hts_code_matching(user_input, options)
        if selected_option:
            return selected_option
        
        # Use Claude for semantic matching if available
        if self.claude_client:
            selected_option = self._claude_match_selection(user_input, options)
            if selected_option:
                return selected_option
        
        return None
    
    def _try_numeric_selection(self, user_input: str, options: List[Dict]) -> Optional[Dict]:
        """Try to parse user input as a numeric selection."""
        if user_input.strip().isdigit():
            selection_index = int(user_input.strip()) - 1
            if 0 <= selection_index < len(options):
                return options[selection_index]
        return None
    
    def _try_hts_code_matching(self, user_input: str, options: List[Dict]) -> Optional[Dict]:
        """Try to match user input to an HTS code."""
        for option in options:
            if option['hts_code'] in user_input:
                return option
        return None
    
    def _claude_match_selection(self, user_input: str, options: List[Dict]) -> Optional[Dict]:
        """Use Claude to match user's response to one of the options."""
        try:
            options_text = "\n".join([
                f"{i+1}. {opt['hts_code']}: {opt['description']}"
                for i, opt in enumerate(options)
            ])
            
            prompt = f"""The user needs to select from these HTS classification options:

{options_text}

User's response: "{user_input}"

Which option (1-{len(options)}) best matches the user's response? 
Respond with just the number, or "none" if no clear match."""

            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            if response_text.isdigit():
                selection_index = int(response_text) - 1
                if 0 <= selection_index < len(options):
                    return options[selection_index]
            
            return None
            
        except Exception:
            return None