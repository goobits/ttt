"""
Agents.py - AI that just works

Simple, intuitive interface for AI agents:
    from agents import ai, chat, stream
    
    response = ai("What's the meaning of life?")
    print(response)
"""

# Main API functions
from .api import ai, chat, achat, stream, ai_async, stream_async

# Response type
from .response import AgentResponse

# Model management
from .registry import ModelConfiguration, ModelInfo, get_default_configuration

# Routing
from .routing import ModelRouter

# Errors
from .errors import (
    AgentError,
    AgentAPIError,
    AgentTimeoutError,
    AgentConfigError,
    AgentModelNotFoundError
)

# Utility functions
def list_models():
    """List all available models."""
    config = get_default_configuration()
    return config.list_models()


def get_model_info(name: str):
    """Get detailed information about a model."""
    config = get_default_configuration()
    model = config.get_model(name)
    return {
        "name": model.name,
        "provider": model.provider,
        "aliases": model.aliases,
        "speed": model.speed,
        "quality": model.quality,
        "cost": model.cost,
        "capabilities": model.capabilities
    }


__version__ = "0.1.0"
__all__ = [
    # Main API
    "ai",
    "chat",
    "achat", 
    "stream",
    "ai_async",
    "stream_async",
    
    # Types
    "AgentResponse",
    "ModelConfiguration",
    "ModelInfo",
    "ModelRouter",
    
    # Utilities
    "list_models",
    "get_model_info",
    "get_default_configuration",
    
    # Errors
    "AgentError",
    "AgentAPIError",
    "AgentTimeoutError",
    "AgentConfigError",
    "AgentModelNotFoundError",
]