"""
Smart model routing for Agents.py

Routes queries to appropriate models based on content analysis.
"""

import re
from typing import Dict, List, Optional, Any
from .registry import ModelInfo, ModelConfiguration, get_default_configuration


class ModelRouter:
    """Routes queries to appropriate models based on content analysis."""
    
    # Patterns for different query types
    PATTERNS = {
        "math": [
            r'\b\d+\s*[\+\-\*/]\s*\d+\b',  # Basic arithmetic
            r'\bcalculat\w*\b',  # calculate, calculation
            r'\bmath\w*\b',  # math, mathematical
            r'\bsolve\b',  # solve
            r'\b(?:sum|product|quotient|difference)\b',  # Math terms
            r'\b\d+\s*(?:percent|%)\s*(?:of|off)\b',  # Percentages
            r'\b(?:equation|formula|algebra)\b',  # Math concepts
        ],
        
        "code": [
            r'\b(?:code|program|script|function|class|debug|fix)\b',
            r'\b(?:python|javascript|java|cpp|rust|golang|ruby|php)\b',
            r'```\w*\n',  # Code blocks
            r'\b(?:error|bug|issue|problem)\b.*\b(?:code|script|program)\b',
            r'\b(?:implement|refactor|optimize)\b.*\b(?:code|function|class)\b',
            r'\b(?:syntax|compile|runtime)\b',
        ],
        
        "creative": [
            r'\b(?:write|create|compose|draft)\b.*\b(?:story|poem|article|essay)\b',
            r'\b(?:creative|imagine|fictional|fantasy)\b',
            r'\btell\s+me\s+a\s+story\b',
            r'\b(?:joke|humor|funny|comedy)\b',
            r'\b(?:novel|narrative|plot|character)\b',
        ],
        
        "analysis": [
            r'\b(?:analyze|review|evaluate|assess|critique)\b',
            r'\b(?:summarize|summary|tldr|brief)\b',
            r'\b(?:explain|describe)\b.*\b(?:detail|depth|comprehensive)\b',
            r'\b(?:pros?\s+and\s+cons?|advantages?\s+and\s+disadvantages?)\b',
            r'\b(?:compare|contrast|difference)\b',
        ],
        
        "quick": [
            r'\b(?:what|who|when|where)\s+(?:is|was|are|were)\b',
            r'\b(?:define|definition)\b',
            r'\b(?:yes\s+or\s+no|true\s+or\s+false)\b',
            r'^[\w\s]{1,20}\?$',  # Very short questions
            r'\b(?:capital|population|location)\s+of\b',
        ],
        
        "vision": [
            r'\b(?:image|picture|photo|screenshot|diagram)\b',
            r'\b(?:look|see|analyze|describe)\b.*\b(?:image|picture)\b',
            r'\b(?:vision|visual|view)\b',
        ]
    }
    
    def __init__(self, config: Optional[ModelConfiguration] = None):
        """
        Initialize router with configuration.
        
        Args:
            config: Model configuration to use (defaults to global)
        """
        self.config = config or get_default_configuration()
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Pre-compile regex patterns for efficiency."""
        compiled = {}
        for category, patterns in self.PATTERNS.items():
            compiled[category] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in patterns
            ]
        return compiled
    
    def route(self, prompt: str, context: Optional[List[Dict]] = None, 
              hints: Optional[Dict[str, Any]] = None) -> ModelInfo:
        """
        Route a prompt to the most appropriate model.
        
        Args:
            prompt: The user's prompt
            context: Conversation history if available
            hints: Hints like {"fast": True} or {"quality": True}
        
        Returns:
            ModelInfo for the selected model
        """
        hints = hints or {}
        
        # Honor explicit hints first
        if hints.get("fast"):
            return self.config.find_fastest_model()
        
        if hints.get("quality"):
            return self.config.find_best_quality_model()
        
        # Check if streaming is requested
        if hints.get("streaming"):
            # Prefer models known for good streaming
            query_type = self._classify_query(prompt)
            return self._route_for_streaming(query_type)
        
        # Analyze query type
        query_type = self._classify_query(prompt)
        
        # Route based on query type
        return self._route_by_type(query_type, prompt)
    
    def _classify_query(self, prompt: str) -> str:
        """Classify the type of query based on patterns."""
        prompt_lower = prompt.lower()
        
        # Check each category's patterns
        for category, patterns in self._compiled_patterns.items():
            if any(pattern.search(prompt_lower) for pattern in patterns):
                return category
        
        return "general"
    
    def _route_by_type(self, query_type: str, prompt: str) -> ModelInfo:
        """Route based on query type."""
        # Define preferred models for each type
        routing_map = {
            "math": "gemini-2.0-flash-exp",  # Fast and good at math
            "code": "claude-3-5-sonnet",     # Best for code
            "creative": "claude-3-5-sonnet",  # Creative writing
            "analysis": "gpt-4o",             # Good at analysis
            "quick": "gpt-4o-mini",           # Fast for simple queries
            "vision": "gpt-4o",               # Good vision support
            "general": "claude-3-5-sonnet",   # Default for general queries
        }
        
        preferred_model = routing_map.get(query_type, "claude-3-5-sonnet")
        
        try:
            return self.config.get_model(preferred_model)
        except Exception:
            # Fallback to default if preferred model not available
            return self.config.get_default_model()
    
    def _route_for_streaming(self, query_type: str) -> ModelInfo:
        """Route for streaming requests."""
        # For streaming, prefer models with good streaming support
        # Generally, OpenAI and Anthropic have better streaming than Google
        
        if query_type in ["code", "creative", "analysis"]:
            try:
                return self.config.get_model("claude-3-5-sonnet")
            except Exception:
                pass
        
        # For quick queries, use a fast streaming model
        try:
            return self.config.get_model("gpt-4o-mini")
        except Exception:
            return self.config.get_default_model()


# Module-level router instance to avoid repeated instantiation
_default_router = ModelRouter()


def get_default_router() -> ModelRouter:
    """Get the default router instance."""
    return _default_router