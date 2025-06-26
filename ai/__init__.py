"""
The Unified AI Library

A single, elegant interface for local and cloud AI models.
"""

from .api import ask, stream, chat
from .models import AIResponse, ImageInput
from .config import configure, model_registry
from .backends import LocalBackend, CloudBackend
from .plugins import register_backend, discover_plugins, load_plugin
from .chat import PersistentChatSession
from .exceptions import (
    AIError,
    BackendError,
    BackendNotAvailableError,
    BackendConnectionError,
    BackendTimeoutError,
    ModelError,
    ModelNotFoundError,
    ModelNotSupportedError,
    ConfigurationError,
    APIKeyError,
    ConfigFileError,
    ValidationError,
    InvalidPromptError,
    InvalidParameterError,
    ResponseError,
    EmptyResponseError,
    ResponseParsingError,
    FeatureNotAvailableError,
    MultiModalError,
    RateLimitError,
    QuotaExceededError,
    PluginError,
    PluginLoadError,
    PluginValidationError,
    SessionError,
    SessionNotFoundError,
    SessionLoadError,
    SessionSaveError,
)

# Auto-load built-in tools when the library is imported
from .tools.builtins import load_builtin_tools

load_builtin_tools()

__version__ = "0.1.0"
__all__ = [
    "ask",
    "stream",
    "chat",
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
