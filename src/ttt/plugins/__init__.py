"""Plugin system for TTT."""

from .loader import discover_plugins, load_plugin, register_backend

__all__ = ["discover_plugins", "load_plugin", "register_backend"]