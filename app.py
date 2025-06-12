"""
Conversational HTS Backend API

This uses your existing LangGraph agent to provide the full conversational
experience with clarifying questions, turn limits, and intelligent responses.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from typing import Dict, List, Optional
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from langgraph_hts_agent import LangGraphHTSAgent
    from csv_hts_loader import CSVHTSLoader
except ImportError as e:
    print(f"❌ Could not import required modules: {e}")
    print("Make sure src/langgraph_hts_agent.py and src/csv_hts_loader.py exist.")
    sys.exit(1)

# Configure clean logging
logging.basicConfig(level=logging.WARNING)
for logger_name in ['anthropic', 'urllib3', 'requests']:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"])

class ConversationalHTSAPI:
    """
    API wrapper for the LangGraph HTS Agent with full conversational capabilities.
    """
    
    def __init__(self):
        """Initialize with your existing LangGraph agent"""
        self.agent = None
        self.conversation_sessions = {}  # Store conversation states by session ID
        self.is_ready = False
        
        try:
            print("🔄 Initializing LangGraph HTS Agent...")
            self.agent = LangGraphHTSAgent()
            
            if self.agent.initialize():
                self.is_ready = True
                print("✅ Conversational HTS API ready")
                if self.agent.claude_client:
                    print("🤖 Claude AI enabled for intelligent conversations")
                else:
                    print("⚠️ Running in fallback mode (no Claude API)")
            else:
                print("❌ Failed to initialize LangGraph agent")
        except Exception as e:
            print(f"❌ Error initializing: {e}")
    
    def process_message(self, user_input: str, session_id: str = "default") -> Dict:
        """
        Process user message with full conversational capabilities.
        
        This handles:
        - Initial classification attempts vs continued conversations
        - Clarifying questions
        - Turn limits (3 attempts)
        - Multiple option selection
        - Conversation memory
        """
        if not self.is_ready:
            return {
                "success": False,
                "error": "Agent not ready"
            }
        
        try:
            # Get existing conversation state for this session
            existing_conversation_state = self.conversation_sessions.get(session_id, None)
            
            # Determine if this is a new conversation or continuation
            is_new_conversation = existing_conversation_state is None
            is_continuation = not is_new_conversation
            
            print(f"🔍 Session {session_id}:")
            print(f"   - Input: '{user_input}'")
            print(f"   - New conversation: {is_new_conversation}")
            print(f"   - Continuation: {is_continuation}")
            if existing_conversation_state:
                conv_history = existing_conversation_state.get('conversation_history', [])
                current_turn = existing_conversation_state.get('current_turn', 1)
                original_commodity = existing_conversation_state.get('original_commodity', 'unknown')
                print(f"   - Existing history: {len(conv_history)} entries")
                print(f"   - Current turn: {current_turn}")
                print(f"   - Original commodity: '{original_commodity}'")
            
            # If this is a continuation, we need to properly build conversation history
            if is_continuation:
                # Add the current user input to conversation history
                conversation_history = existing_conversation_state.get('conversation_history', [])
                current_turn = existing_conversation_state.get('current_turn', 1)
                
                # Add this response to history
                conversation_history.append({
                    "user": user_input,
                    "turn": current_turn,
                    "timestamp": "now"
                })
                
                # Increment turn for next response
                next_turn = current_turn + 1
                
                # Update the conversation state with new history and turn
                updated_conversation_state = {
                    **existing_conversation_state,
                    "conversation_history": conversation_history,
                    "current_turn": next_turn,
                    "user_input": user_input  # Update current input
                }
                
                print(f"   - Updated conversation history: {len(conversation_history)} entries")
                print(f"   - Next turn will be: {next_turn}")
                
                # Pass the updated state to the agent
                result = self.agent.classify_commodity(user_input, updated_conversation_state)
            else:
                # New conversation - no existing state
                print("   - Starting fresh conversation")
                result = self.agent.classify_commodity(user_input, None)
            
            if result["success"]:
                # CRITICAL: Update conversation state for this session
                new_conversation_state = result.get("conversation_state", {})
                
                # Ensure we preserve the conversation history we built
                if is_continuation and conversation_history:
                    new_conversation_state["conversation_history"] = conversation_history
                    new_conversation_state["current_turn"] = next_turn
                
                self.conversation_sessions[session_id] = new_conversation_state
                
                print(f"🔍 Session {session_id}: Final state saved")
                print(f"   - History entries: {len(new_conversation_state.get('conversation_history', []))}")
                print(f"   - Current turn: {new_conversation_state.get('current_turn', 1)}")
                
                # Clean and format the response for React frontend
                clean_response = self._format_for_frontend(result["result"], user_input)
                
                return {
                    "success": True,
                    **clean_response,
                    "session_id": session_id,
                    "conversation_state": new_conversation_state,
                    "is_continuation": is_continuation,
                    "debug_info": {
                        "history_length": len(new_conversation_state.get('conversation_history', [])),
                        "turn": new_conversation_state.get('current_turn', 1)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Classification failed"),
                    "session_id": session_id
                }
                
        except Exception as e:
            print(f"❌ Error in process_message: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Processing failed: {str(e)}",
                "session_id": session_id
            }
    
    def _format_for_frontend(self, agent_result: Dict, user_input: str) -> Dict:
        """
        Format LangGraph agent results for React frontend consumption.
        """
        response = {
            "type": "unknown",
            "message": "",
            "data": {}
        }
        
        # Check if we have clarifying questions
        if agent_result.get("clarifying_questions"):
            response["type"] = "clarifying_questions"
            response["message"] = "I need more information to classify your product accurately."
            response["data"] = {
                "questions": agent_result["clarifying_questions"],
                "turn": agent_result.get("current_turn", 1),
                "original_query": user_input
            }
            return response
        
        # Check if we have final classification
        if agent_result.get("classification_complete") and agent_result.get("final_classification"):
            final = agent_result["final_classification"]
            
            if final.get("type") == "multiple_options":
                # Multiple options for user to choose from
                response["type"] = "multiple_options"
                response["message"] = final.get("message", "Please select the best match:")
                response["data"] = {
                    "options": self._format_options(final.get("options", [])),
                    "selection_needed": True
                }
            else:
                # Single final classification
                response["type"] = "final_classification"
                response["message"] = "Classification complete!"
                response["data"] = {
                    "results": [self._format_single_result(final)],
                    "classification_complete": True
                }
            
            return response
        
        # Check if we have current candidates to show
        if agent_result.get("current_hts_candidates"):
            candidates = agent_result["current_hts_candidates"]
            
            # If high confidence, show as results
            high_confidence = [c for c in candidates if c.get("confidence_score", 0) >= 85]
            
            if high_confidence:
                response["type"] = "high_confidence_results"
                response["message"] = f"Found {len(high_confidence)} high-confidence match{'es' if len(high_confidence) > 1 else ''}."
                response["data"] = {
                    "results": [self._format_single_result(c) for c in high_confidence[:3]]
                }
            else:
                response["type"] = "low_confidence_results"
                response["message"] = "Found some possible matches, but confidence is low."
                response["data"] = {
                    "results": [self._format_single_result(c) for c in candidates[:3]]
                }
            
            return response
        
        # Default case - no results
        response["type"] = "no_results"
        response["message"] = "No HTS classifications found. Try being more specific."
        response["data"] = {}
        
        return response
    
    def _format_single_result(self, result: Dict) -> Dict:
        """Format a single HTS result for the frontend"""
        return {
            "hts_code": result.get("hts_code", ""),
            "description": result.get("description", ""),
            "effective_duty": result.get("effective_duty", "Unknown"),
            "confidence_score": int(result.get("confidence_score", 0)),  # Convert to int
            "match_type": result.get("match_type", "unknown"),
            "chapter": result.get("chapter", ""),
            "unit": result.get("full_details", {}).get("unit", ""),
            "special_duty": result.get("full_details", {}).get("stored_special_duty", ""),
            "duty_source": result.get("full_details", {}).get("duty_source", ""),
            "indent_level": int(result.get("full_details", {}).get("indent", 0)),  # Convert to int
        }
    
    def _format_options(self, options: List[Dict]) -> List[Dict]:
        """Format multiple options for user selection"""
        formatted_options = []
        
        for i, option in enumerate(options):
            formatted_options.append({
                "index": i + 1,
                "hts_code": option.get("hts_code", ""),
                "description": option.get("description", ""),
                "effective_duty": option.get("effective_duty", "Unknown"),
                "confidence_score": int(option.get("confidence_score", 0)),  # Convert to int
                "match_type": option.get("match_type", "unknown")
            })
        
        return formatted_options
    
    def clear_session(self, session_id: str):
        """Clear conversation state for a session"""
        if session_id in self.conversation_sessions:
            del self.conversation_sessions[session_id]

# Initialize the API
print("🚀 Initializing Conversational HTS API...")
api = ConversationalHTSAPI()

@app.route('/api/classify', methods=['POST'])
def classify_product():
    """
    Main classification endpoint with conversation support.
    
    Expected JSON: 
    {
        "query": "product description",
        "session_id": "optional_session_id"
    }
    
    Returns various response types based on conversation state.
    """
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON"
            }), 400
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'query' field in request"
            }), 400
        
        query = data['query']
        session_id = data.get('session_id', 'default')
        
        # Process with conversation support
        result = api.process_message(query, session_id)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/api/session/clear', methods=['POST'])
def clear_session():
    """Clear conversation session to start fresh"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id', 'default')
        
        print(f"🔄 Clearing session: {session_id}")
        api.clear_session(session_id)
        
        return jsonify({
            "success": True,
            "message": f"Session {session_id} cleared"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to clear session: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check with agent status"""
    return jsonify({
        "status": "healthy",
        "agent_ready": api.is_ready,
        "claude_enabled": api.agent.claude_client is not None if api.agent else False,
        "version": "1.0.0"
    })

@app.route('/api/capabilities', methods=['GET'])
def get_capabilities():
    """Get API capabilities"""
    return jsonify({
        "success": True,
        "capabilities": {
            "conversational": True,
            "clarifying_questions": True,
            "turn_limits": True,
            "multiple_options": True,
            "claude_ai": api.agent.claude_client is not None if api.agent else False,
            "hierarchy_search": True,
            "fuzzy_matching": True
        }
    })

@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        "name": "Conversational HTS Classifier API",
        "version": "1.0.0",
        "description": "Full conversational HTS classification with LangGraph agent",
        "endpoints": {
            "POST /api/classify": "Classify products with conversation support",
            "POST /api/session/clear": "Clear conversation session",
            "GET /api/health": "Health check",
            "GET /api/capabilities": "Get API capabilities"
        },
        "features": [
            "Intelligent clarifying questions",
            "3-turn conversation limit", 
            "Multiple option selection",
            "Claude AI integration",
            "Conversation memory"
        ],
        "agent_ready": api.is_ready
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 Conversational HTS Classifier API")
    print("="*60)
    print(f"🔧 Agent Status: {'✅ Ready' if api.is_ready else '❌ Not Ready'}")
    if api.agent:
        print(f"🧠 Claude AI: {'✅ Enabled' if api.agent.claude_client else '❌ Disabled'}")
    print("\n📡 API Endpoints:")
    print("   POST /api/classify - Conversational classification")
    print("   POST /api/session/clear - Clear conversation")
    print("   GET  /api/health - Health check")
    print("   GET  /api/capabilities - Feature list")
    print("\n🎯 Features:")
    print("   ✅ Clarifying questions")
    print("   ✅ 3-turn conversation limit")
    print("   ✅ Multiple option selection")
    print("   ✅ Conversation memory")
    print("   ✅ Hierarchy navigation")
    print("\n🌐 Frontend: http://localhost:5173")
    print("="*60)
    
    app.run(
        debug=True,
        host='0.0.0.0',
        port=8000,
        threaded=True
    )