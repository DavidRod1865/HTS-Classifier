"""
LangGraph HTS Classification Agent - Refactored and Optimized

Cleaned workflow:
1. Claude reviews user input and confirms what they want to import
2. Perform hierarchy search to find HTS codes
3. If <3 codes found OR confidence <85%, ask clarifying questions (max 3)
4. If ≥85% confidence codes found, present them for user selection
5. Final classification

This follows a logical customs broker workflow with improved code organization.
"""

from typing import TypedDict, List, Dict, Optional
import json
import os
import logging

from langgraph.graph import StateGraph, END
from anthropic import Anthropic

from constants import *
from csv_hts_loader import CSVHTSLoader
from search_engine import HTSSearchEngine
from question_generator import QuestionGenerator, ResponseMatcher
from product_classifier import ProductClassifier


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HTSClassificationState(TypedDict):
    """State that flows through the LangGraph workflow."""
    
    # User input and conversation
    user_input: str
    confirmed_product: str 
    conversation_history: List[Dict[str, str]]
    current_turn: int
    
    # HTS search results
    current_hts_candidates: List[Dict]
    confidence_score: float
    
    # Decision making
    next_action: str
    clarifying_questions: List[str]
    
    # Final results
    final_classification: Optional[Dict]
    classification_complete: bool


class LangGraphHTSAgent:
    """
    Refactored LangGraph HTS Classification Agent with improved modularity.
    """
    
    def __init__(self, csv_file_path: str = None, anthropic_api_key: str = None):
        """Initialize the LangGraph agent with Anthropic Claude."""
        self.hts_loader = CSVHTSLoader(csv_file_path)
        
        # Initialize Anthropic client
        self.claude_client = self._initialize_claude_client()
        self.claude_model = self._detect_best_model()
        
        # Initialize component modules
        self.search_engine = HTSSearchEngine(self.hts_loader)
        self.question_generator = QuestionGenerator(self.claude_client, self.claude_model)
        self.response_matcher = ResponseMatcher(self.claude_client, self.claude_model)
        self.product_classifier = ProductClassifier(self.hts_loader, self.claude_client, self.claude_model)
        
        self.workflow = None
        self.app = None
    
    def _initialize_claude_client(self) -> Optional[Anthropic]:
        """Initialize Anthropic client with proper error handling."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning(ERROR_MESSAGES['no_api_key'])
            return None
        else:
            return Anthropic(api_key=api_key)
    
    def _detect_best_model(self) -> Optional[str]:
        """Detect the best available Claude model."""
        if not self.claude_client:
            return None
        
        for model in DEFAULT_CLAUDE_MODELS:
            try:
                self.claude_client.messages.create(
                    model=model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "test"}]
                )
                logger.info(SUCCESS_MESSAGES['model_detected'].format(model))
                return model
            except Exception as e:
                if "not_found_error" not in str(e):
                    break
        
        logger.warning(ERROR_MESSAGES['no_model_found'])
        return DEFAULT_CLAUDE_MODELS[0]
    
    def initialize(self) -> bool:
        """Initialize the HTS data and build the workflow."""
        logger.info("🤖 Initializing Refactored LangGraph HTS Agent...")
        
        # Load HTS data
        if not self.hts_loader.load_data():
            logger.error(ERROR_MESSAGES['initialization_failed'])
            return False
        
        # Build the workflow
        self._build_workflow()
        
        logger.info(SUCCESS_MESSAGES['agent_ready'])
        return True
    
    def _build_workflow(self):
        """Build the LangGraph workflow with proper node organization."""
        workflow = StateGraph(HTSClassificationState)
        
        # Add workflow nodes
        workflow.add_node(WORKFLOW_NODES['CONFIRM_PRODUCT'], self.confirm_product_understanding)
        workflow.add_node(WORKFLOW_NODES['HIERARCHY_SEARCH'], self.perform_hierarchy_search)
        workflow.add_node(WORKFLOW_NODES['GENERATE_QUESTIONS'], self.generate_clarifying_questions)
        workflow.add_node(WORKFLOW_NODES['PROCESS_RESPONSE'], self.process_user_response)
        workflow.add_node(WORKFLOW_NODES['FINAL_CLASSIFY'], self.final_classification)
        workflow.add_node(WORKFLOW_NODES['HANDLE_SELECTION'], self.handle_user_selection)
        
        # Set entry point
        workflow.set_entry_point(WORKFLOW_NODES['CONFIRM_PRODUCT'])
        
        # Add conditional edges
        self._add_workflow_edges(workflow)
        
        # Compile the workflow
        self.app = workflow.compile()
    
    def _add_workflow_edges(self, workflow):
        """Add all conditional edges to the workflow."""
        workflow.add_conditional_edges(
            WORKFLOW_NODES['CONFIRM_PRODUCT'],
            self.after_confirmation,
            {
                WORKFLOW_ACTIONS['SEARCH']: WORKFLOW_NODES['HIERARCHY_SEARCH'],
                WORKFLOW_ACTIONS['PROCESS_RESPONSE']: WORKFLOW_NODES['PROCESS_RESPONSE']
            }
        )
        
        workflow.add_conditional_edges(
            WORKFLOW_NODES['HIERARCHY_SEARCH'],
            self.after_search,
            {
                WORKFLOW_ACTIONS['QUESTION']: WORKFLOW_NODES['GENERATE_QUESTIONS'],
                WORKFLOW_ACTIONS['CLASSIFY']: WORKFLOW_NODES['FINAL_CLASSIFY']
            }
        )
        
        workflow.add_conditional_edges(
            WORKFLOW_NODES['GENERATE_QUESTIONS'],
            self.after_questions,
            {
                WORKFLOW_ACTIONS['WAIT_RESPONSE']: END,
                WORKFLOW_ACTIONS['CLASSIFY']: WORKFLOW_NODES['FINAL_CLASSIFY']
            }
        )
        
        workflow.add_conditional_edges(
            WORKFLOW_NODES['PROCESS_RESPONSE'],
            self.after_response,
            {
                WORKFLOW_ACTIONS['SEARCH']: WORKFLOW_NODES['HIERARCHY_SEARCH'],
                WORKFLOW_ACTIONS['QUESTION']: WORKFLOW_NODES['GENERATE_QUESTIONS'],
                WORKFLOW_ACTIONS['CLASSIFY']: WORKFLOW_NODES['FINAL_CLASSIFY']
            }
        )
        
        workflow.add_conditional_edges(
            WORKFLOW_NODES['FINAL_CLASSIFY'],
            self.after_classification,
            {
                WORKFLOW_ACTIONS['COMPLETE']: END,
                WORKFLOW_ACTIONS['SELECTION_NEEDED']: WORKFLOW_NODES['HANDLE_SELECTION']
            }
        )
        
        workflow.add_edge(WORKFLOW_NODES['HANDLE_SELECTION'], END)
    
    # Workflow Node Implementations
    
    def confirm_product_understanding(self, state: HTSClassificationState) -> HTSClassificationState:
        """Step 1: Claude reviews and confirms understanding of what user wants to import."""
        logger.info("🔍 Step 1: Confirming product understanding...")
        
        user_input = state["user_input"]
        conversation_history = state.get("conversation_history", [])
        
        # Check if this is a continuation
        if len(conversation_history) > 0:
            logger.info("   Detected continuation - processing user response")
            return {
                **state,
                "next_action": WORKFLOW_ACTIONS['PROCESS_RESPONSE']
            }
        
        # Confirm understanding using product classifier
        confirmed_product = self.product_classifier.confirm_product_understanding(user_input)
        logger.info(f"   Confirmed product: {confirmed_product}")
        
        return {
            **state,
            "confirmed_product": confirmed_product,
            "next_action": WORKFLOW_ACTIONS['SEARCH']
        }
    
    def perform_hierarchy_search(self, state: HTSClassificationState) -> HTSClassificationState:
        """Step 2: Perform comprehensive hierarchy search for HTS codes."""
        logger.info("🔍 Step 2: Performing hierarchy search...")
        
        confirmed_product = state.get("confirmed_product", state["user_input"])
        
        # Perform search using search engine
        try:
            search_results = self.search_engine.comprehensive_search(confirmed_product)
        except Exception as e:
            logger.error(ERROR_MESSAGES['search_error'].format(e))
            search_results = []
        
        # Analyze results
        search_results = search_results or []
        high_confidence_results = [
            r for r in search_results 
            if r.get('confidence_score', 0) >= HIGH_CONFIDENCE_THRESHOLD
        ]
        avg_confidence = (
            sum(r['confidence_score'] for r in search_results[:5]) / min(5, len(search_results))
            if search_results else 0
        )
        
        logger.info(f"   Found {len(search_results)} total candidates")
        logger.info(f"   High confidence (≥{HIGH_CONFIDENCE_THRESHOLD}%): {len(high_confidence_results)}")
        logger.info(f"   Average confidence: {avg_confidence:.1f}%")
        
        # Determine next action
        next_action = self._determine_search_action(search_results, high_confidence_results)
        
        return {
            **state,
            "current_hts_candidates": search_results[:MAX_CLASSIFICATION_OPTIONS],
            "confidence_score": avg_confidence,
            "next_action": next_action
        }
    
    def generate_clarifying_questions(self, state: HTSClassificationState) -> HTSClassificationState:
        """Step 3: Generate up to 3 clarifying questions to narrow down classification."""
        logger.info("🔍 Step 3: Generating clarifying questions...")
        
        current_turn = state.get("current_turn", 1)
        candidates = state.get("current_hts_candidates", [])
        confirmed_product = state.get("confirmed_product", state["user_input"])
        conversation_history = state.get("conversation_history", [])
        
        # Generate questions using question generator
        questions = self.question_generator.generate_questions(
            confirmed_product, candidates, conversation_history, current_turn
        )
        
        # Check if we've hit the turn limit
        if current_turn > MAX_CONVERSATION_TURNS:
            return {
                **state,
                "next_action": WORKFLOW_ACTIONS['CLASSIFY'],
                "clarifying_questions": []
            }
        
        return {
            **state,
            "clarifying_questions": questions,
            "next_action": WORKFLOW_ACTIONS['WAIT_RESPONSE']
        }
    
    def process_user_response(self, state: HTSClassificationState) -> HTSClassificationState:
        """Process user's response to clarifying questions."""
        logger.info("🔍 Processing user response...")
        
        user_input = state["user_input"]
        conversation_history = state.get("conversation_history", [])
        current_turn = state.get("current_turn", 1)
        confirmed_product = state.get("confirmed_product", user_input)
        
        # Add response to conversation history
        conversation_history.append({
            "user": user_input,
            "turn": current_turn,
            "timestamp": "now"
        })
        
        # Increment turn counter
        new_turn = current_turn + 1
        logger.info(f"   Turn progression: {current_turn} → {new_turn}")
        
        return {
            **state,
            "conversation_history": conversation_history,
            "current_turn": new_turn,
            "confirmed_product": confirmed_product,
            "next_action": WORKFLOW_ACTIONS['SEARCH']
        }
    
    def final_classification(self, state: HTSClassificationState) -> HTSClassificationState:
        """Step 4: Present high-confidence results or top options for selection."""
        logger.info("🔍 Step 4: Final classification...")
        
        candidates = state.get("current_hts_candidates", [])
        current_turn = state.get("current_turn", 1)
        
        if not candidates:
            return {
                **state,
                "final_classification": None,
                "classification_complete": False
            }
        
        # Create classification using product classifier
        final_classification = self.product_classifier.create_final_classification(
            candidates, current_turn
        )
        
        if final_classification:
            selection_needed = final_classification.get("selection_needed", False)
            classification_complete = not selection_needed
            
            return {
                **state,
                "final_classification": final_classification,
                "classification_complete": classification_complete,
                "next_action": WORKFLOW_ACTIONS['AWAIT_SELECTION'] if selection_needed else WORKFLOW_ACTIONS['COMPLETE']
            }
        
        return {
            **state,
            "final_classification": None,
            "classification_complete": False
        }
    
    def handle_user_selection(self, state: HTSClassificationState) -> HTSClassificationState:
        """Handle user selection from presented options."""
        logger.info("🔍 Processing user selection...")
        
        user_input = state["user_input"]
        final_classification = state.get("final_classification", {})
        options = final_classification.get("options", [])
        
        # Try to match user selection
        selected_option = self.response_matcher.match_user_selection(user_input, options)
        
        if selected_option:
            # Valid selection made
            result = self.product_classifier.create_user_selection_result(selected_option)
            return {
                **state,
                "final_classification": result,
                "classification_complete": True
            }
        else:
            # Invalid selection
            invalid_response = self.product_classifier.create_invalid_selection_response(options)
            return {
                **state,
                "final_classification": {
                    **final_classification,
                    **invalid_response
                },
                "classification_complete": False
            }
    
    # Conditional Edge Functions
    
    def after_confirmation(self, state: HTSClassificationState) -> str:
        """Decide what to do after product confirmation."""
        next_action = state.get("next_action", WORKFLOW_ACTIONS['SEARCH'])
        return next_action if next_action in [WORKFLOW_ACTIONS['PROCESS_RESPONSE'], WORKFLOW_ACTIONS['SEARCH']] else WORKFLOW_ACTIONS['SEARCH']
    
    def after_search(self, state: HTSClassificationState) -> str:
        """Decide what to do after hierarchy search."""
        return state.get("next_action", WORKFLOW_ACTIONS['QUESTION'])
    
    def after_questions(self, state: HTSClassificationState) -> str:
        """Decide what to do after generating questions."""
        return state.get("next_action", WORKFLOW_ACTIONS['WAIT_RESPONSE'])
    
    def after_response(self, state: HTSClassificationState) -> str:
        """Decide what to do after processing user response."""
        return state.get("next_action", WORKFLOW_ACTIONS['SEARCH'])
    
    def after_classification(self, state: HTSClassificationState) -> str:
        """Decide what to do after classification."""
        final_classification = state.get("final_classification", {})
        if final_classification.get("selection_needed", False):
            return WORKFLOW_ACTIONS['SELECTION_NEEDED']
        else:
            return WORKFLOW_ACTIONS['COMPLETE']
    
    # Helper Methods
    
    def _determine_search_action(self, search_results: List[Dict], high_confidence_results: List[Dict]) -> str:
        """Determine the next action based on search results."""
        if len(high_confidence_results) >= 1:
            return WORKFLOW_ACTIONS['CLASSIFY']
        elif len(search_results) < 3:
            return WORKFLOW_ACTIONS['QUESTION']
        else:
            return WORKFLOW_ACTIONS['QUESTION']
    
    # Main Interface Methods
    
    def classify_commodity(self, user_input: str, conversation_state: Dict = None) -> Dict:
        """Main interface for commodity classification using the refactored workflow."""
        
        # Determine if this is a new commodity or a continuation
        is_new_commodity = conversation_state is None or conversation_state.get("conversation_history", []) == []
        
        # Initialize state
        initial_state = {
            "user_input": user_input,
            "confirmed_product": "",
            "conversation_history": conversation_state.get("conversation_history", []) if conversation_state else [],
            "current_turn": conversation_state.get("current_turn", 1) if conversation_state else 1,
            "current_hts_candidates": [],
            "confidence_score": 0.0,
            "next_action": WORKFLOW_ACTIONS['SEARCH'] if not is_new_commodity else "confirm",
            "clarifying_questions": [],
            "final_classification": None,
            "classification_complete": False
        }
        
        # For continuing conversations, process the response
        if not is_new_commodity:
            initial_state["next_action"] = "process"
        
        # Run the workflow
        try:
            result = self.app.invoke(initial_state)
            return {
                "success": True,
                "result": result,
                "conversation_state": {
                    "conversation_history": result.get("conversation_history", []),
                    "current_turn": result.get("current_turn", 1),
                    "confirmed_product": result.get("confirmed_product", user_input)
                }
            }
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "conversation_state": conversation_state
            }


# Example usage and testing
def main():
    """Test the refactored LangGraph HTS Agent."""
    logger.info("🚀 Testing Refactored LangGraph HTS Agent")
    logger.info("=" * 50)
    
    agent = LangGraphHTSAgent()
    
    if not agent.initialize():
        logger.error(ERROR_MESSAGES['initialization_failed'])
        return
    
    # Test inputs
    test_inputs = [
        "tires",
        "laptop computer", 
        "wooden chairs"
    ]
    
    for test_input in test_inputs:
        logger.info(f"\n🎯 Testing: '{test_input}'")
        logger.info("-" * 30)
        
        result = agent.classify_commodity(test_input)
        
        if result["success"]:
            state = result["result"]
            logger.info("✅ Workflow completed")
            
            confirmed_product = state.get("confirmed_product", "")
            if confirmed_product:
                logger.info(f"📝 Confirmed product: {confirmed_product}")
            
            candidates = state.get("current_hts_candidates", [])
            logger.info(f"🔍 Candidates found: {len(candidates)}")
            
            if candidates:
                high_confidence = [c for c in candidates if c.get('confidence_score', 0) >= HIGH_CONFIDENCE_THRESHOLD]
                logger.info(f"⭐ High confidence (≥{HIGH_CONFIDENCE_THRESHOLD}%): {len(high_confidence)}")
            
            if state.get("final_classification"):
                final = state["final_classification"]
                if final.get("type") in [CLASSIFICATION_TYPES['HIGH_CONFIDENCE_OPTIONS'], CLASSIFICATION_TYPES['FINAL_OPTIONS']]:
                    logger.info(f"🎯 Presenting {len(final.get('options', []))} options for selection")
                else:
                    logger.info(f"🎯 Final Classification: {final.get('hts_code')}")
            elif state.get("clarifying_questions"):
                questions = state["clarifying_questions"]
                logger.info(f"❓ Generated {len(questions)} questions:")
                for i, q in enumerate(questions, 1):
                    logger.info(f"   {i}. {q}")
        else:
            logger.error(f"❌ Error: {result['error']}")


if __name__ == "__main__":
    main()