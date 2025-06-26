"""Backend implementations for different AI providers."""

from .base import BaseBackend
from .cloud import CloudBackend

# Conditionally import local backend
try:
    from .local import LocalBackend

    HAS_LOCAL_BACKEND = True
    __all__ = ["BaseBackend", "CloudBackend", "LocalBackend"]
except ImportError:
    LocalBackend = None
    HAS_LOCAL_BACKEND = False
    __all__ = ["BaseBackend", "CloudBackend"]
