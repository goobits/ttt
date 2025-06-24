"""
LiteLLM backend implementation with true async support.
"""

from typing import List, Dict, Any, Generator, AsyncGenerator

try:
    from litellm import completion, acompletion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

from . import Backend
from ..errors import AgentError, AgentAPIError
from ..registry import ModelInfo


class LiteLLMBackend(Backend):
    """Backend using LiteLLM for unified API access."""
    
    def __init__(self, model_info: ModelInfo):
        """
        Initialize LiteLLM backend.
        
        Args:
            model_info: Model configuration
        """
        if not LITELLM_AVAILABLE:
            raise AgentError("litellm is required. Install with: pip install litellm")
        
        super().__init__(model_info)
        # Use the provider_name which is already in the correct format
        self.model_name = model_info.provider_name
    
    def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Get a completion using LiteLLM."""
        try:
            response = completion(
                model=self.model_name,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
            )
            return response.choices[0].message.content
        except Exception as e:
            raise AgentAPIError(f"LiteLLM error: {e}")
    
    async def acomplete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Get an async completion using LiteLLM."""
        try:
            response = await acompletion(
                model=self.model_name,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
            )
            return response.choices[0].message.content
        except Exception as e:
            raise AgentAPIError(f"LiteLLM async error: {e}")
    
    def stream(self, messages: List[Dict[str, str]], **kwargs) -> Generator[str, None, None]:
        """Stream a completion using LiteLLM."""
        try:
            stream = completion(
                model=self.model_name,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"[Streaming error: {e}]"
    
    async def astream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Async stream a completion using LiteLLM."""
        try:
            stream = await acompletion(
                model=self.model_name,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"[Async streaming error: {e}]"