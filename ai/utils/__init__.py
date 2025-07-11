"""Utility modules for the AI library."""

import asyncio
import sys
from typing import Awaitable, TypeVar

from .logger import get_logger
from rich.console import Console

console = Console()

T = TypeVar("T")

def run_async(coro: Awaitable[T]) -> T:
    """
    Runs an awaitable from a synchronous context and returns the result.

    This function is designed to bridge async and sync code. It will
    start a new event loop if one is not already running. If a loop is
    running, it will run the coroutine in a thread-safe manner.
    """
    try:
        # Check if an event loop is already running in the current thread.
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'get_running_loop' fails if there is no running loop
        # No running loop, so we can create and run a new one.
        # This is the typical case for scripts and simple applications.
        if sys.version_info >= (3, 7):
            return asyncio.run(coro)
        else:
            # Fallback for older Python versions
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
                asyncio.set_event_loop(None)
    else:
        # A loop is already running. We can't use asyncio.run().
        # We need to run the coroutine in a new thread to avoid deadlock.
        import concurrent.futures
        import threading
        # Create a new thread with its own event loop
        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
                asyncio.set_event_loop(None)
        # Use ThreadPoolExecutor to run the coroutine in a separate thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()

__all__ = ["get_logger", "console", "run_async"]
