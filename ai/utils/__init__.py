"""Utility modules for the AI library."""

from .logger import get_logger
from rich.console import Console

console = Console()

__all__ = ["get_logger", "console"]