"""
Response object for Agents.py

Defines the AgentResponse class that behaves like a string but carries metadata.
"""

from typing import Optional, Any, Dict, Union
from dataclasses import dataclass, field


@dataclass
class AgentResponse:
    """
    Response object that behaves like a string but carries metadata.
    
    This class provides a dual interface:
    - Acts like a string for simple use cases
    - Provides rich metadata for advanced use cases
    
    Examples:
        >>> response = ai("Hello")
        >>> print(response)  # Just prints the text
        >>> print(response.model)  # Access metadata
        >>> print(response.time)  # Time taken
        >>> if response:  # Check if successful
        ...     process(response)
    """
    content: str
    model: str
    time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    _error: Optional[Exception] = None
    
    def __str__(self) -> str:
        """Make the response printable as just the content."""
        return self.content
    
    def __repr__(self) -> str:
        """Show useful debug info."""
        if self._error:
            return f"AgentResponse(error={self._error}, model={self.model})"
        return f"AgentResponse(model={self.model}, time={self.time:.2f}s, length={len(self.content)})"
    
    def __bool__(self) -> bool:
        """Check if we got a valid response."""
        return bool(self.content) and self._error is None
    
    def __len__(self) -> int:
        """Get the length of the response content."""
        return len(self.content)
    
    def __contains__(self, item: str) -> bool:
        """Check if text is in the response."""
        return item in self.content
    
    def __getitem__(self, key: Union[int, slice]) -> str:
        """Allow slicing the response like a string."""
        return self.content[key]
    
    def __eq__(self, other) -> bool:
        """Compare responses by content."""
        if isinstance(other, str):
            return self.content == other
        elif isinstance(other, AgentResponse):
            return self.content == other.content
        return False
    
    @property
    def failed(self) -> bool:
        """Check if the request failed."""
        return self._error is not None
    
    @property
    def error(self) -> Optional[str]:
        """Get error message if failed."""
        return str(self._error) if self._error else None
    
    @property
    def tokens(self) -> Optional[int]:
        """Get token count if available."""
        return self.metadata.get('tokens')
    
    @property
    def cost(self) -> Optional[float]:
        """Get cost if available."""
        return self.metadata.get('cost')
    
    @property
    def provider(self) -> Optional[str]:
        """Get the provider used."""
        return self.metadata.get('provider')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to a dictionary."""
        return {
            "content": self.content,
            "model": self.model,
            "time": self.time,
            "metadata": self.metadata,
            "error": self.error
        }