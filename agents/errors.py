"""
Error types for Agents.py
"""


class AgentError(Exception):
    """Base exception for all agent errors."""
    pass


class AgentAPIError(AgentError):
    """Error from the underlying API provider."""
    pass


class AgentTimeoutError(AgentError):
    """Request timed out."""
    pass


class AgentConfigError(AgentError):
    """Configuration error (missing API keys, etc)."""
    pass


class AgentModelNotFoundError(AgentError):
    """Requested model not found."""
    pass