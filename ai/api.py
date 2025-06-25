"""Core API functions providing the main user interface."""

import asyncio
from typing import AsyncIterator, Optional, Iterator, Union, List
from contextlib import asynccontextmanager, contextmanager

from .models import AIResponse, ImageInput
from .backends import BaseBackend, LocalBackend, CloudBackend
from .routing import router
from .plugins import discover_plugins
from .utils import get_logger
from .chat import PersistentChatSession


logger = get_logger(__name__)

# Initialize plugins on module load
try:
    discover_plugins()
except Exception as e:
    logger.debug(f"Plugin discovery failed: {e}")


def _cleanup_aiohttp_sessions_sync(loop):
    """Synchronously cleanup aiohttp sessions and tasks to prevent warnings."""
    import gc
    import warnings
    import logging
    
    # Temporarily disable logging to prevent cleanup noise
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)
    
    # Suppress specific aiohttp cleanup warnings during our own cleanup
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*Task was destroyed.*")
        warnings.filterwarnings("ignore", message=".*ClientSession.*")
        warnings.filterwarnings("ignore", message=".*BaseConnector.*")
        warnings.filterwarnings("ignore", message=".*_wait_for_close.*")
        
        # More aggressive cleanup approach
        try:
            # Get all pending tasks and cancel them
            all_tasks = list(asyncio.all_tasks(loop))
            for task in all_tasks:
                if not task.done():
                    task.cancel()
            
            # Force wait for cancellation with multiple attempts
            if all_tasks:
                for attempt in range(3):
                    try:
                        remaining_tasks = [t for t in all_tasks if not t.done()]
                        if not remaining_tasks:
                            break
                        
                        loop.run_until_complete(
                            asyncio.wait_for(
                                asyncio.gather(*remaining_tasks, return_exceptions=True),
                                timeout=0.1
                            )
                        )
                        break
                    except (asyncio.TimeoutError, asyncio.CancelledError, RuntimeError):
                        continue  # Try again with shorter timeout
                        
        except RuntimeError:
            pass  # Event loop may be closing
        
        # Force cleanup of aiohttp objects using gc
        try:
            import aiohttp
            
            # Multiple garbage collection passes to ensure cleanup
            for _ in range(3):
                gc.collect()
                
                # Find and close any remaining aiohttp objects
                for obj in gc.get_objects():
                    try:
                        if hasattr(obj, '__class__'):
                            class_name = obj.__class__.__name__
                            
                            # Handle ClientSession cleanup
                            if isinstance(obj, aiohttp.ClientSession) and not getattr(obj, '_closed', True):
                                try:
                                    # Try to close without creating new loop
                                    if hasattr(obj, '_connector') and obj._connector:
                                        obj._connector._close()
                                    obj._closed = True
                                except (AttributeError, RuntimeError):
                                    pass  # Expected during cleanup
                            
                            # Handle BaseConnector cleanup
                            elif class_name == 'TCPConnector' or 'Connector' in class_name:
                                if hasattr(obj, '_close') and not getattr(obj, '_closed', True):
                                    try:
                                        obj._close()
                                    except (AttributeError, RuntimeError):
                                        pass  # Expected during cleanup
                                        
                    except (TypeError, AttributeError, RuntimeError):
                        pass  # Ignore individual cleanup failures
                        
        except ImportError:
            pass  # aiohttp not available
        
        # Final garbage collection
        gc.collect()
        
    # Restore logging level
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def _get_default_backend() -> BaseBackend:
    """Get the default backend (local if available, otherwise cloud)."""
    try:
        backend = LocalBackend()
        if backend.is_available:
            return backend
    except Exception as e:
        logger.debug(f"Local backend not available: {e}")
    
    return CloudBackend()


def ask(
    prompt: Union[str, List[Union[str, ImageInput]]],
    *,
    model: Optional[str] = None,
    system: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    backend: Optional[Union[str, BaseBackend]] = None,
    fast: bool = False,
    quality: bool = False,
    tools: Optional[List] = None,
    **kwargs
) -> AIResponse:
    """
    Ask a question and get a response. The simplest way to use AI.
    
    Examples:
        >>> response = ask("What is Python?")
        >>> print(response)
        
        >>> response = ask("Fix this code", system="You are a code reviewer")
        >>> print(f"Model: {response.model}, Time: {response.time}s")
        
        >>> response = ask("Quick question", fast=True)
        >>> response = ask("Complex analysis", quality=True)
        
        >>> # Multi-modal with images
        >>> response = ask([
        ...     "What's in this image?",
        ...     ImageInput("photo.jpg")
        ... ], model="gpt-4-vision-preview")
        
        >>> # Multiple images
        >>> response = ask([
        ...     "Compare these images:",
        ...     ImageInput("image1.png"),
        ...     ImageInput("image2.png")
        ... ], backend="cloud")
        
        >>> # With tools
        >>> def get_weather(city: str) -> str:
        ...     return f"Weather in {city}: 72°F, sunny"
        >>> response = ask("What's the weather in NYC?", tools=[get_weather])
        >>> print(f"Called {len(response.tool_calls)} tools")
    
    Args:
        prompt: Your question - can be a string or list of content (text/images)
        model: Specific model to use (optional)
        system: System prompt to set context (optional)
        temperature: Sampling temperature 0-1 (optional)
        max_tokens: Maximum tokens to generate (optional)
        backend: Backend to use, "local", "cloud", "auto", or Backend instance (optional)
        fast: Prefer speed over quality (optional)
        quality: Prefer quality over speed (optional)
        tools: List of functions/tools the AI can call (optional)
        **kwargs: Additional backend-specific parameters
        
    Returns:
        AIResponse that behaves like a string but contains metadata
    """
    # Use smart routing
    backend_instance, resolved_model = router.smart_route(
        prompt,
        model=model,
        backend=backend,
        prefer_speed=fast,
        prefer_quality=quality,
        **kwargs
    )
    
    # Run async function in sync context with proper cleanup
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            backend_instance.ask(
                prompt,
                model=resolved_model,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                **kwargs
            )
        )
        
        # Properly cleanup aiohttp sessions and tasks
        _cleanup_aiohttp_sessions_sync(loop)
        
        return result
    finally:
        loop.close()


def stream(
    prompt: Union[str, List[Union[str, ImageInput]]],
    *,
    model: Optional[str] = None,
    system: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    backend: Optional[Union[str, BaseBackend]] = None,
    fast: bool = False,
    quality: bool = False,
    tools: Optional[List] = None,
    **kwargs
) -> Iterator[str]:
    """
    Stream a response token by token.
    
    Examples:
        >>> for chunk in stream("Tell me a story"):
        ...     print(chunk, end="", flush=True)
        
        >>> # Multi-modal streaming
        >>> for chunk in stream([
        ...     "Describe this image:",
        ...     ImageInput("photo.jpg")
        ... ], model="gpt-4-vision-preview"):
        ...     print(chunk, end="", flush=True)
    
    Args:
        prompt: Your question - can be a string or list of content (text/images)
        model: Specific model to use (optional)
        system: System prompt to set context (optional)
        temperature: Sampling temperature 0-1 (optional)
        max_tokens: Maximum tokens to generate (optional)
        backend: Backend to use, "local", "cloud", "auto", or Backend instance (optional)
        fast: Prefer speed over quality (optional)
        quality: Prefer quality over speed (optional)
        tools: List of functions/tools the AI can call (optional)
        **kwargs: Additional backend-specific parameters
        
    Yields:
        String chunks as they arrive
    """
    # Use smart routing
    backend_instance, resolved_model = router.smart_route(
        prompt,
        model=model,
        backend=backend,
        prefer_speed=fast,
        prefer_quality=quality,
        **kwargs
    )
    
    # Convert async generator to sync generator
    async def _async_stream():
        async for chunk in backend_instance.astream(
            prompt,
            model=resolved_model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs
        ):
            yield chunk
    
    # Run async generator in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async_gen = _async_stream()
        while True:
            try:
                chunk = loop.run_until_complete(async_gen.__anext__())
                yield chunk
            except StopAsyncIteration:
                break
        
        # Cleanup after streaming is complete
        _cleanup_aiohttp_sessions_sync(loop)
    finally:
        loop.close()


class ChatSession:
    """
    A chat session that maintains conversation history.
    
    This class manages a conversation context, allowing for multi-turn
    conversations with persistent memory.
    """
    
    def __init__(
        self,
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        backend: Optional[Union[str, BaseBackend]] = None,
        **kwargs
    ):
        """
        Initialize a chat session.
        
        Args:
            system: System prompt to set the assistant's behavior
            model: Default model to use for this session
            backend: Backend to use for this session
            **kwargs: Additional parameters passed to each request
        """
        self.system = system
        self.model = model
        self.kwargs = kwargs
        self.history = []
        
        # Handle backend selection
        if isinstance(backend, str):
            if backend == "local":
                self.backend = LocalBackend()
            else:
                raise ValueError(f"Unknown backend: {backend}")
        elif isinstance(backend, BaseBackend):
            self.backend = backend
        else:
            self.backend = _get_default_backend()
    
    def ask(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """
        Ask a question in this chat session.
        
        Args:
            prompt: Your message/question
            model: Override the session's default model
            **kwargs: Additional parameters for this request
            
        Returns:
            AIResponse with the assistant's reply
        """
        # Add user message to history
        self.history.append({"role": "user", "content": prompt})
        
        # Build conversation context
        if len(self.history) == 1:
            # First message, just use the prompt
            full_prompt = prompt
        else:
            # Build conversation history
            conversation = []
            for msg in self.history[:-1]:  # All but the last message
                if msg["role"] == "user":
                    conversation.append(f"Human: {msg['content']}")
                else:
                    conversation.append(f"Assistant: {msg['content']}")
            
            conversation.append(f"Human: {prompt}")
            full_prompt = "\n\n".join(conversation)
        
        # Merge parameters
        params = {**self.kwargs, **kwargs}
        
        # Make the request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                self.backend.ask(
                    full_prompt,
                    model=model or self.model,
                    system=self.system,
                    **params
                )
            )
            
            # Cleanup aiohttp sessions
            _cleanup_aiohttp_sessions_sync(loop)
        finally:
            loop.close()
        
        # Add assistant response to history
        self.history.append({"role": "assistant", "content": str(response)})
        
        return response
    
    def stream(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Stream a response in this chat session.
        
        Args:
            prompt: Your message/question  
            model: Override the session's default model
            **kwargs: Additional parameters for this request
            
        Yields:
            String chunks as they arrive
        """
        # Add user message to history
        self.history.append({"role": "user", "content": prompt})
        
        # Build conversation context (same logic as ask)
        if len(self.history) == 1:
            full_prompt = prompt
        else:
            conversation = []
            for msg in self.history[:-1]:
                if msg["role"] == "user":
                    conversation.append(f"Human: {msg['content']}")
                else:
                    conversation.append(f"Assistant: {msg['content']}")
            
            conversation.append(f"Human: {prompt}")
            full_prompt = "\n\n".join(conversation)
        
        # Merge parameters
        params = {**self.kwargs, **kwargs}
        
        # Stream the response and collect it
        response_parts = []
        
        async def _async_stream():
            async for chunk in self.backend.astream(
                full_prompt,
                model=model or self.model,
                system=self.system,
                **params
            ):
                response_parts.append(chunk)
                yield chunk
        
        # Run async generator in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async_gen = _async_stream()
            while True:
                try:
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    yield chunk
                except StopAsyncIteration:
                    break
            
            # Cleanup after streaming is complete
            _cleanup_aiohttp_sessions_sync(loop)
        finally:
            loop.close()
        
        # Add complete response to history
        full_response = "".join(response_parts)
        self.history.append({"role": "assistant", "content": full_response})
    
    def clear(self) -> None:
        """Clear the conversation history."""
        self.history = []


@contextmanager
def chat(
    *,
    system: Optional[str] = None,
    model: Optional[str] = None,
    backend: Optional[Union[str, BaseBackend]] = None,
    persist: bool = False,
    session_id: Optional[str] = None,
    **kwargs
):
    """
    Context manager for chat sessions.
    
    Examples:
        >>> with chat() as session:
        ...     response = session.ask("Hello!")
        ...     print(response)
        ...     response = session.ask("What's 2+2?")
        ...     print(response)
        
        >>> with chat(system="You are a helpful coding assistant") as session:
        ...     response = session.ask("Write a Python function")
        ...     print(response)
        
        >>> # Persistent session that can be saved
        >>> with chat(persist=True) as session:
        ...     session.ask("Remember this: My name is Alice")
        ...     session.save("alice_chat.json")
        
        >>> # Resume a saved session
        >>> from ai.chat import PersistentChatSession
        >>> session = PersistentChatSession.load("alice_chat.json")
        >>> session.ask("What's my name?")  # Will remember it's Alice
    
    Args:
        system: System prompt to set the assistant's behavior
        model: Default model to use for this session
        backend: Backend to use for this session
        persist: Use PersistentChatSession for save/load support
        session_id: Unique identifier for persistent sessions
        **kwargs: Additional parameters passed to each request
        
    Yields:
        ChatSession or PersistentChatSession instance
    """
    if persist:
        session = PersistentChatSession(
            system=system,
            model=model,
            backend=backend,
            session_id=session_id,
            **kwargs
        )
    else:
        session = ChatSession(
            system=system,
            model=model,
            backend=backend,
            **kwargs
        )
    try:
        yield session
    finally:
        # Clean up if needed
        pass


# Async versions for advanced users
async def ask_async(
    prompt: str,
    *,
    model: Optional[str] = None,
    system: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    backend: Optional[Union[str, BaseBackend]] = None,
    **kwargs
) -> AIResponse:
    """Async version of ask()."""
    # Handle backend selection
    if isinstance(backend, str):
        if backend == "local":
            backend_instance = LocalBackend()
        else:
            raise ValueError(f"Unknown backend: {backend}")
    elif isinstance(backend, BaseBackend):
        backend_instance = backend
    else:
        backend_instance = _get_default_backend()
    
    return await backend_instance.ask(
        prompt,
        model=model,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


async def stream_async(
    prompt: str,
    *,
    model: Optional[str] = None,
    system: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    backend: Optional[Union[str, BaseBackend]] = None,
    **kwargs
) -> AsyncIterator[str]:
    """Async version of stream()."""
    # Handle backend selection
    if isinstance(backend, str):
        if backend == "local":
            backend_instance = LocalBackend()
        else:
            raise ValueError(f"Unknown backend: {backend}")
    elif isinstance(backend, BaseBackend):
        backend_instance = backend
    else:
        backend_instance = _get_default_backend()
    
    async for chunk in backend_instance.astream(
        prompt,
        model=model,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    ):
        yield chunk


@asynccontextmanager
async def achat(
    *,
    system: Optional[str] = None,
    model: Optional[str] = None,
    backend: Optional[Union[str, BaseBackend]] = None,
    **kwargs
):
    """Async context manager for chat sessions."""
    session = ChatSession(
        system=system,
        model=model,
        backend=backend,
        **kwargs
    )
    try:
        yield session
    finally:
        pass