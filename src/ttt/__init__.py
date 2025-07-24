"""
The Unified AI Library

A single, elegant interface for local and cloud AI models.
"""

from .core.api import ChatSession, achat, ask, ask_async, chat, stream, stream_async
from .backends import CloudBackend, LocalBackend
from .session.chat import PersistentChatSession
from .config.schema import configure


# Import model_registry lazily to avoid import-time initialization
def _get_model_registry():
    from .config.schema import model_registry

    return model_registry


# Create a lazy proxy for model_registry
class _ModelRegistryProxy:
    def __getattr__(self, name):
        return getattr(_get_model_registry(), name)


model_registry = _ModelRegistryProxy()
from .core.exceptions import (
    AIError,
    APIKeyError,
    BackendConnectionError,
    BackendError,
    BackendNotAvailableError,
    BackendTimeoutError,
    ConfigFileError,
    ConfigurationError,
    EmptyResponseError,
    FeatureNotAvailableError,
    InvalidParameterError,
    InvalidPromptError,
    ModelError,
    ModelNotFoundError,
    ModelNotSupportedError,
    MultiModalError,
    PluginError,
    PluginLoadError,
    PluginValidationError,
    QuotaExceededError,
    RateLimitError,
    ResponseError,
    ResponseParsingError,
    SessionError,
    SessionLoadError,
    SessionNotFoundError,
    SessionSaveError,
    ValidationError,
)
from .core.models import AIResponse, ImageInput
from .plugins import discover_plugins, load_plugin, register_backend

# Auto-load built-in tools when the library is imported
from .tools.builtins import load_builtin_tools

load_builtin_tools()

__version__ = "1.0.0rc3"
__all__ = [
    "ask",
    "stream",
    "chat",
    "ask_async",
    "stream_async",
    "achat",
    "ChatSession",
    "AIResponse",
    "ImageInput",
    "PersistentChatSession",
    "configure",
    "LocalBackend",
    "CloudBackend",
    "model_registry",
    "register_backend",
    "discover_plugins",
    "load_plugin",
    # Exceptions
    "AIError",
    "BackendError",
    "BackendNotAvailableError",
    "BackendConnectionError",
    "BackendTimeoutError",
    "ModelError",
    "ModelNotFoundError",
    "ModelNotSupportedError",
    "ConfigurationError",
    "APIKeyError",
    "ConfigFileError",
    "ValidationError",
    "InvalidPromptError",
    "InvalidParameterError",
    "ResponseError",
    "EmptyResponseError",
    "ResponseParsingError",
    "FeatureNotAvailableError",
    "MultiModalError",
    "RateLimitError",
    "QuotaExceededError",
    "PluginError",
    "PluginLoadError",
    "PluginValidationError",
    "SessionError",
    "SessionNotFoundError",
    "SessionLoadError",
    "SessionSaveError",
]
