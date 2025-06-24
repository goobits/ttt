"""
Mock backend for testing.
"""

import asyncio
from typing import List, Dict, Any, Generator, AsyncGenerator, Optional

from . import Backend
from ..registry import ModelInfo


class MockBackend(Backend):
    """Mock backend for testing without API calls."""
    
    def __init__(self, model_info: ModelInfo, responses: Optional[Dict[str, str]] = None):
        """
        Initialize mock backend.
        
        Args:
            model_info: Model configuration
            responses: Dict mapping prompts to responses
        """
        super().__init__(model_info)
        self.responses = responses or {"default": "Mock response"}
        self.call_history = []
    
    def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Return a mock response."""
        last_message = messages[-1]["content"]
        self.call_history.append({"messages": messages, "kwargs": kwargs})
        
        # Check for specific responses
        for key, response in self.responses.items():
            if key in last_message:
                return response
        
        return self.responses.get("default", "Mock response")
    
    async def acomplete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Return a mock response asynchronously."""
        # Simulate some async work
        await asyncio.sleep(0.01)
        return self.complete(messages, **kwargs)
    
    def stream(self, messages: List[Dict[str, str]], **kwargs) -> Generator[str, None, None]:
        """Stream a mock response word by word."""
        response = self.complete(messages, **kwargs)
        for word in response.split():
            yield word + " "
    
    async def astream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Async stream a mock response."""
        response = await self.acomplete(messages, **kwargs)
        for word in response.split():
            yield word + " "
            await asyncio.sleep(0.001)  # Simulate streaming delay