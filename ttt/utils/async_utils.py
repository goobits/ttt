"""Optimized async utilities for better performance."""

import asyncio
import threading
import concurrent.futures
import sys
import atexit
from typing import Awaitable, TypeVar

T = TypeVar("T")

# Global shared event loop and thread
_background_loop = None
_background_thread = None
_executor = None
_lock = threading.Lock()


def _start_background_loop():
    """Start the background event loop in a dedicated thread."""
    global _background_loop, _background_thread, _executor
    
    if _background_loop is not None:
        return  # Already started
    
    def run_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        global _background_loop
        _background_loop = loop
        try:
            loop.run_forever()
        finally:
            loop.close()
    
    _background_thread = threading.Thread(target=run_loop, daemon=True)
    _background_thread.start()
    
    # Wait for the loop to be ready
    while _background_loop is None:
        pass
    
    # Create a thread pool executor for non-async operations
    _executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def _stop_background_loop():
    """Stop the background event loop and cleanup resources."""
    global _background_loop, _background_thread, _executor
    
    if _background_loop is not None:
        _background_loop.call_soon_threadsafe(_background_loop.stop)
        _background_thread.join(timeout=1.0)
        _background_loop = None
        _background_thread = None
    
    if _executor is not None:
        _executor.shutdown(wait=False)
        _executor = None


# Register cleanup function
atexit.register(_stop_background_loop)


def run_coro_in_background(coro: Awaitable[T]) -> T:
    """
    Run a coroutine in the shared background event loop.
    
    This is much more efficient than creating a new event loop
    for every synchronous call.
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    with _lock:
        if _background_loop is None:
            _start_background_loop()
    
    # Submit the coroutine to the background loop
    future = asyncio.run_coroutine_threadsafe(coro, _background_loop)
    return future.result()


def optimized_run_async(coro: Awaitable[T]) -> T:
    """
    Optimized version of run_async that reuses a background event loop.
    
    This function provides better performance by avoiding the overhead
    of creating new event loops for every call.
    """
    try:
        # Check if an event loop is already running in the current thread
        asyncio.get_running_loop()
        # If we get here, we're already in an async context
        # Use the background loop approach
        return run_coro_in_background(coro)
    except RuntimeError:
        # No running loop, so we can create and run a new one
        # For the main thread, still use asyncio.run for simplicity
        if sys.version_info >= (3, 7):
            return asyncio.run(coro)
        else:
            # For Python 3.6 compatibility
            return asyncio.run(coro)