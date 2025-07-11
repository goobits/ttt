"""Core API functions providing the main user interface."""

import asyncio
from typing import AsyncIterator, Optional, Iterator, Union, List
from contextlib import asynccontextmanager, contextmanager

from .models import AIResponse, ImageInput
from .backends import BaseBackend, LocalBackend, CloudBackend
from .routing import router
from .plugins import discover_plugins
from .utils import get_logger, run_async
from .chat import PersistentChatSession


logger = get_logger(__name__)

# Initialize plugins on module load
try:
    discover_plugins()
except Exception as e:
    logger.debug(f"Plugin discovery failed: {e}")




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
    **kwargs,
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
    logger.debug(f"API ask() called with: model={model}, max_tokens={max_tokens}, temperature={temperature}")
    
    # Use smart routing
    backend_instance, resolved_model = router.smart_route(
        prompt,
        model=model,
        backend=backend,
        prefer_speed=fast,
        prefer_quality=quality,
        **kwargs,
    )

    async def _ask_wrapper():
        return await backend_instance.ask(
            prompt,
            model=resolved_model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        )

    return run_async(_ask_wrapper())


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
    **kwargs,
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
        **kwargs,
    )

    # This is the async generator from the backend
    async_gen = backend_instance.astream(
        prompt,
        model=resolved_model,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
        tools=tools,
        **kwargs,
    )

    # We create a bridge to pull from the async generator synchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        while True:
            try:
                # Run the __anext__ coroutine to get the next item
                chunk = loop.run_until_complete(async_gen.__anext__())
                yield chunk
            except StopAsyncIteration:
                # The async generator is exhausted
                break
    finally:
        # Cleanly close the loop when done
        loop.close()
        asyncio.set_event_loop(None)


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
        tools: Optional[List] = None,
        **kwargs,
    ):
        """
        Initialize a chat session.

        Args:
            system: System prompt to set the assistant's behavior
            model: Default model to use for this session
            backend: Backend to use for this session
            tools: List of functions/tools the AI can call
            **kwargs: Additional parameters passed to each request
        """
        self.system = system
        self.model = model
        self.kwargs = kwargs
        self.tools = tools
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

    def ask(self, prompt: str, *, model: Optional[str] = None, **kwargs) -> AIResponse:
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
        async def _ask_wrapper():
            return await self.backend.ask(
                full_prompt,
                model=model or self.model,
                system=self.system,
                tools=self.tools,
                **params,
            )
            
        response = run_async(_ask_wrapper())

        # Add assistant response to history
        self.history.append({"role": "assistant", "content": str(response)})

        return response

    def stream(
        self, prompt: str, *, model: Optional[str] = None, **kwargs
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

        # This is the async generator from the backend
        async_gen = self.backend.astream(
            full_prompt,
            model=model or self.model,
            system=self.system,
            tools=self.tools,
            **params,
        )

        # We create a bridge to pull from the async generator synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            while True:
                try:
                    # Run the __anext__ coroutine to get the next item
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    response_parts.append(chunk)
                    yield chunk
                except StopAsyncIteration:
                    # The async generator is exhausted
                    break
        finally:
            # Cleanly close the loop when done
            loop.close()
            asyncio.set_event_loop(None)

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
    tools: Optional[List] = None,
    **kwargs,
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

        >>> # Chat with tools
        >>> def get_weather(city: str) -> str:
        ...     return f"Weather in {city}: 72°F, sunny"
        >>> with chat(tools=[get_weather]) as session:
        ...     response = session.ask("What's the weather in NYC?")
        ...     print(response)

    Args:
        system: System prompt to set the assistant's behavior
        model: Default model to use for this session
        backend: Backend to use for this session
        persist: Use PersistentChatSession for save/load support
        session_id: Unique identifier for persistent sessions
        tools: List of functions/tools the AI can call
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
            tools=tools,
            **kwargs,
        )
    else:
        session = ChatSession(
            system=system, model=model, backend=backend, tools=tools, **kwargs
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
    **kwargs,
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
        **kwargs,
    )


async def stream_async(
    prompt: str,
    *,
    model: Optional[str] = None,
    system: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    backend: Optional[Union[str, BaseBackend]] = None,
    **kwargs,
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
        **kwargs,
    ):
        yield chunk


@asynccontextmanager
async def achat(
    *,
    system: Optional[str] = None,
    model: Optional[str] = None,
    backend: Optional[Union[str, BaseBackend]] = None,
    **kwargs,
):
    """Async context manager for chat sessions."""
    session = ChatSession(system=system, model=model, backend=backend, **kwargs)
    try:
        yield session
    finally:
        pass
