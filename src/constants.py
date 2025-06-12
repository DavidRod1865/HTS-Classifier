"""
Constants for HTS Classification System

This module contains all configuration constants, magic numbers, and
reusable strings used throughout the HTS classification system.
"""

# API and Model Configuration
DEFAULT_CLAUDE_MODELS = [
    "claude-3-5-sonnet-20241022",
    "claude-3-sonnet-20240229",
]

# Search Configuration
DEFAULT_MAX_SEARCH_RESULTS = 25
DEFAULT_FUZZY_SEARCH_RESULTS = 20
DEFAULT_MIN_FUZZY_SCORE = 50
DEFAULT_CHAPTER_SEARCH_RESULTS = 10
DEFAULT_ENHANCED_SEARCH_RESULTS = 5

# Classification Configuration
HIGH_CONFIDENCE_THRESHOLD = 85
MEDIUM_CONFIDENCE_THRESHOLD = 70
LOW_CONFIDENCE_THRESHOLD = 40
MAX_CONVERSATION_TURNS = 3
MAX_CLASSIFICATION_OPTIONS = 15
MAX_DISPLAY_OPTIONS = 5

# HTS Code Validation
MIN_COMPLETE_HTS_LENGTH = 8
MIN_CHAPTER_LENGTH = 2
MIN_HEADING_LENGTH = 4
MIN_DETAIL_INDENT_LEVEL = 2

# Search Weights and Scores
EXACT_MATCH_CONFIDENCE = 95
FUZZY_MATCH_MAX_CONFIDENCE = 90
FUZZY_MATCH_MIN_CONFIDENCE = 50
SEMANTIC_SEARCH_MAX_CONFIDENCE = 85
CHAPTER_FALLBACK_CONFIDENCE = 70
EXACT_MATCH_SCORE_WEIGHT = 60
PARTIAL_MATCH_SCORE_WEIGHT = 10
MAX_PARTIAL_MATCH_BONUS = 25

# Question Generation
MAX_CLARIFYING_QUESTIONS = 3
MIN_QUESTION_LENGTH = 10

# Common Stop Words
COMMON_STOP_WORDS = {
    'the', 'of', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with', 
    'by', 'from', 'a', 'an', 'other', 'parts', 'nesoi', 'nesi'
}

# Product Category Mappings
PRODUCT_SYNONYMS = {
    'tire': ['tire', 'tyre', 'pneumatic', 'rubber', 'vehicle', 'automotive', 'wheel'],
    'tires': ['tire', 'tyre', 'pneumatic', 'rubber', 'vehicle', 'automotive', 'wheel'],
    'computer': ['computer', 'computing', 'processor', 'electronic', 'data', 'automatic', 'digital'],
    'laptop': ['computer', 'portable', 'notebook', 'electronic', 'automatic', 'processing'],
    'phone': ['telephone', 'cellular', 'mobile', 'communication', 'apparatus'],
    'smartphone': ['telephone', 'cellular', 'mobile', 'communication', 'electronic', 'apparatus'],
    'chair': ['chair', 'seating', 'furniture', 'seat'],
    'chairs': ['chair', 'seating', 'furniture', 'seat'],
    'table': ['table', 'furniture', 'desk'],
    'tables': ['table', 'furniture', 'desk'],
    'clothing': ['clothing', 'garment', 'apparel', 'wearing'],
    'shirt': ['shirt', 'garment', 'clothing', 'wearing'],
    'shoes': ['footwear', 'shoe', 'boot'],
    'book': ['book', 'printed', 'publication'],
    'books': ['book', 'printed', 'publication'],
    'bottle': ['bottle', 'container', 'receptacle', 'vessel', 'packaging'],
    'bottles': ['bottle', 'container', 'receptacle', 'vessel', 'packaging'],
}

# Chapter Targeting for Products
PRODUCT_CHAPTER_MAPPING = {
    'tire': {'40': 60, '87': 30},  # Rubber products, Vehicles
    'tires': {'40': 60, '87': 30},
    'rubber': {'40': 50},
    'computer': {'84': 50, '85': 30},  # Machinery, Electrical
    'laptop': {'84': 60},
    'phone': {'85': 60},  # Electrical equipment
    'smartphone': {'85': 60},
    'chair': {'94': 60},  # Furniture
    'furniture': {'94': 50},
    'wooden': {'44': 40, '94': 30},  # Wood, Furniture
    'metal': {'72': 30, '73': 30},  # Iron/Steel, Articles of iron/steel
    'plastic': {'39': 40},  # Plastics
    'electronic': {'85': 40, '84': 30},  # Electrical, Machinery
    'bottle': ['39', '70'],  # Plastics, Glass
    'bottles': ['39', '70'],
}

# Material-based Classification
MATERIAL_KEYWORDS = {
    'rubber': ['rubber', 'tire', 'tyre', 'pneumatic'],
    'wooden': ['wood', 'timber', 'furniture'],
    'metal': ['metal', 'steel', 'iron', 'aluminum'],
    'plastic': ['plastic', 'polymer'],
    'electronic': ['electronic', 'electrical', 'digital'],
    'textile': ['textile', 'fabric', 'clothing'],
    'glass': ['glass', 'bottle', 'container'],
}

# Error Messages
ERROR_MESSAGES = {
    'no_api_key': "Warning: No / Incorrect Anthropic API key provided.",
    'no_model_found': "⚠️ Could not detect working Claude model",
    'search_error': "❌ Search error: {}",
    'claude_error': "⚠️ Claude {} error: {}",
    'relevance_check_error': "⚠️ Error in relevance check: {}",
    'initialization_failed': "❌ Failed to initialize agent",
    'agent_not_ready': "Agent not ready",
    'classification_failed': "Classification failed",
    'processing_failed': "Processing failed: {}",
}

# Success Messages
SUCCESS_MESSAGES = {
    'model_detected': "✅ Using Claude model: {}",
    'agent_ready': "✅ Simplified LangGraph HTS Agent ready!",
    'classifier_ready': "✅ Classifier ready!",
}

# Workflow Node Names
WORKFLOW_NODES = {
    'CONFIRM_PRODUCT': 'confirm_product',
    'HIERARCHY_SEARCH': 'hierarchy_search',
    'GENERATE_QUESTIONS': 'generate_questions',
    'PROCESS_RESPONSE': 'process_response',
    'FINAL_CLASSIFY': 'final_classify',
    'HANDLE_SELECTION': 'handle_selection',
}

# Workflow Actions
WORKFLOW_ACTIONS = {
    'SEARCH': 'search',
    'QUESTION': 'question',
    'CLASSIFY': 'classify',
    'PROCESS_RESPONSE': 'process_response',
    'WAIT_RESPONSE': 'wait_response',
    'COMPLETE': 'complete',
    'SELECTION_NEEDED': 'selection_needed',
    'AWAIT_SELECTION': 'await_selection',
}

# Classification Types
CLASSIFICATION_TYPES = {
    'HIGH_CONFIDENCE_OPTIONS': 'high_confidence_options',
    'FINAL_OPTIONS': 'final_options',
    'SINGLE_CLASSIFICATION': 'single_classification',
    'USER_SELECTED': 'user_selected',
    'MULTIPLE_OPTIONS': 'multiple_options',
}

# API Response Types
API_RESPONSE_TYPES = {
    'CLARIFYING_QUESTIONS': 'clarifying_questions',
    'FINAL_CLASSIFICATION': 'final_classification',
    'MULTIPLE_OPTIONS': 'multiple_options',
    'HIGH_CONFIDENCE_RESULTS': 'high_confidence_results',
    'LOW_CONFIDENCE_RESULTS': 'low_confidence_results',
    'NO_RESULTS': 'no_results',
}

# Question Focus by Turn
QUESTION_FOCUS = {
    1: "Ask about basic product category, material, or primary function",
    2: "Ask about specific features, dimensions, or technical specifications", 
    3: "Ask decisive questions to distinguish between remaining options"
}

# Fallback Questions by Turn
FALLBACK_QUESTIONS = {
    1: [
        "What is the primary material composition of your product?",
        "What is the intended commercial use or application?",
        "Is this product new, used, or refurbished?"
    ],
    2: [
        "What are the specific dimensions or technical specifications?",
        "Does your product have any special features or certifications?",
        "What industry or sector will this product be used in?"
    ],
    3: [
        "Which product description most accurately matches yours?",
        "Are there any unique distinguishing features?",
        "What is the exact end-use application?"
    ]
}

# File Paths
DEFAULT_CSV_PATHS = [
    "hts_2025_revision_13.csv",
    "data/hts_2025_revision_13.csv",
    "hts_data.csv",
    "data/hts_data.csv"
]

# API Configuration
API_CONFIG = {
    'CORS_ORIGINS': ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    'DEFAULT_SESSION_ID': 'default',
    'DEFAULT_PORT': 8000,
    'DEFAULT_HOST': '0.0.0.0',
}