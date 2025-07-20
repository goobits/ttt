"""Optimized async utilities for better performance."""

import asyncio
import atexit
import concurrent.futures
import threading
from typing import Awaitable, TypeVar, cast

T = TypeVar("T")

# Global shared event loop and thread
_background_loop = None
_background_thread = None
_executor = None
_lock = threading.Lock()


def _start_background_loop() -> None:
    """Start the background event loop in a dedicated thread."""
    global _background_loop, _background_thread, _executor

    if _background_loop is not None:
        return  # Already started

    def run_loop() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Set up custom exception handler to suppress aiohttp task warnings
        def custom_exception_handler(
            loop: asyncio.AbstractEventLoop, context: dict
        ) -> None:
            # Suppress specific aiohttp task destruction warnings
            message = context.get("message", "")
            exception = context.get("exception")
            if "Task was destroyed but it is pending" in message or (
                exception and "Task was destroyed but it is pending" in str(exception)
            ):
                return  # Ignore this specific error
            # For other exceptions, use default behavior
            loop.default_exception_handler(context)

        loop.set_exception_handler(custom_exception_handler)

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


def _stop_background_loop() -> None:
    """Stop the background event loop and cleanup resources."""
    global _background_loop, _background_thread, _executor

    if _background_loop is not None:
        # Cancel all pending tasks more gracefully
        def cancel_tasks() -> None:
            tasks = asyncio.all_tasks(_background_loop)
            for task in tasks:
                if not task.done():
                    task.cancel()

            # Schedule loop stop after tasks are cancelled
            async def stop_when_ready() -> None:
                # Wait briefly for cancellations to complete
                await asyncio.sleep(0.1)
                if _background_loop is not None:
                    _background_loop.stop()

            asyncio.create_task(stop_when_ready())

        _background_loop.call_soon_threadsafe(cancel_tasks)
        # Give more time for graceful shutdown
        if _background_thread:
            _background_thread.join(timeout=2.0)
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
    if _background_loop is None:
        raise RuntimeError("Background loop not initialized")

    # Convert Awaitable to coroutine if needed
    if asyncio.iscoroutine(coro):
        future: concurrent.futures.Future[T] = asyncio.run_coroutine_threadsafe(
            coro, _background_loop
        )
    else:
        # If it's not a coroutine but an awaitable, we need to wrap it
        async def _wrapper() -> T:
            return await coro

        future = asyncio.run_coroutine_threadsafe(_wrapper(), _background_loop)

    result = future.result()
    return result


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
        # Convert Awaitable to coroutine if needed
        if asyncio.iscoroutine(coro):
            result = asyncio.run(coro)
            return cast(T, result)
        else:
            # If it's not a coroutine but an awaitable, wrap it
            async def _wrapper() -> T:
                return await coro

            return asyncio.run(_wrapper())
