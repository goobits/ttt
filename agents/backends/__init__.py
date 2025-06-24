"""
Backend implementations for AI providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, AsyncGenerator

from ..errors import AgentError
from ..registry import ModelInfo


class Backend(ABC):
    """Abstract base class for AI provider backends."""
    
    def __init__(self, model_info: ModelInfo):
        """
        Initialize backend with model information.
        
        Args:
            model_info: Model configuration
        """
        self.model_info = model_info
    
    @abstractmethod
    def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Get a completion from the model.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters
        
        Returns:
            The model's response text
        """
        pass
    
    @abstractmethod
    async def acomplete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Get an async completion from the model.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters
        
        Returns:
            The model's response text
        """
        pass
    
    @abstractmethod
    def stream(self, messages: List[Dict[str, str]], **kwargs) -> Generator[str, None, None]:
        """
        Stream a completion from the model.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters
        
        Yields:
            Response text chunks
        """
        pass
    
    @abstractmethod
    async def astream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """
        Async stream a completion from the model.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters
        
        Yields:
            Response text chunks
        """
        pass


def create_backend(provider: str, model_info: ModelInfo) -> Backend:
    """
    Create a backend for the specified provider.
    
    Args:
        provider: Provider name (openai, anthropic, google, mock)
        model_info: Model configuration
    
    Returns:
        Backend instance
    
    Raises:
        AgentError: If provider is not supported
    """
    if provider == "mock":
        from .mock import MockBackend
        return MockBackend(model_info)
    else:
        # Use LiteLLM for all real providers
        from .litellm import LiteLLMBackend
        return LiteLLMBackend(model_info)