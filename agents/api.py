"""
Main API functions for Agents.py

This module provides the user-facing functions:
- ai(): Simple one-shot queries
- chat(): Conversational context manager
- stream(): Streaming responses
"""

import time
import asyncio
from typing import Optional, Any, Dict, List, Generator, AsyncGenerator
from contextlib import contextmanager, asynccontextmanager

from .response import AgentResponse
from .session import ChatSession
from .routing import get_default_router
from .registry import get_default_configuration
from .backends import create_backend
from .utils import format_prompt_with_context


# Module-level instances to avoid repeated creation
_router = get_default_router()
_config = get_default_configuration()


def ai(prompt: str, *, model: Optional[str] = None, fast: bool = False, 
       quality: bool = False, **kwargs) -> AgentResponse:
    """
    Simple AI query - the main entry point for most users.
    
    This function automatically routes your query to the most appropriate model
    based on the content, or you can specify a model explicitly.
    
    Args:
        prompt: Your question or request
        model: Specific model to use (optional)
        fast: Prefer speed over quality
        quality: Prefer quality over speed
        **kwargs: Additional context (code=, json=, text=, etc)
    
    Returns:
        AgentResponse that acts like a string but has metadata
    
    Examples:
        >>> response = ai("What's Python?")
        >>> print(response)  # Just the text
        >>> print(response.model)  # Which model was used
        >>> print(response.time)  # How long it took
        
        >>> # With context
        >>> response = ai("Explain this code:", code=my_code)
        
        >>> # With specific model
        >>> response = ai("Hello", model="gpt-4")
        
        >>> # With hints
        >>> response = ai("2+2", fast=True)
    """
    start_time = time.time()
    
    # Route to appropriate model
    hints = {"fast": fast, "quality": quality}
    if model:
        model_info = _config.get_model(model)
    else:
        model_info = _router.route(prompt, hints=hints)
    
    # Create backend for this model
    backend = create_backend(model_info.provider, model_info)
    
    # Format prompt with any additional context
    if kwargs:
        prompt = format_prompt_with_context(prompt, kwargs)
    
    try:
        # Get response
        response_text = backend.complete([{"role": "user", "content": prompt}])
        
        response = AgentResponse(
            content=response_text,
            model=model_info.name,
            time=time.time() - start_time,
            metadata={
                "provider": model_info.provider,
                "hints": hints
            }
        )
        
        return response
        
    except Exception as e:
        response = AgentResponse(
            content="",
            model=model_info.name,
            time=time.time() - start_time,
            _error=e
        )
        return response


@contextmanager
def chat(model: Optional[str] = None, system: Optional[str] = None):
    """
    Create a conversation context.
    
    This context manager provides a stateful conversation where each message
    builds on the previous ones. The conversation history is maintained
    automatically.
    
    Args:
        model: Specific model to use for the conversation
        system: System prompt to set the assistant's behavior
    
    Yields:
        ChatSession object that can be called to send messages
    
    Examples:
        >>> with chat() as c:
        ...     c("Hello!")
        ...     c("Tell me a joke")
        ...     response = c("Make it funnier")
        
        >>> with chat(system="You are a Python expert") as expert:
        ...     solution = expert("How do I sort a list?")
        ...     example = expert("Show me an example")
        
        >>> # Save conversation
        >>> with chat() as c:
        ...     c("Important discussion")
        ...     c.save("conversation.json")
    """
    session = ChatSession(model=model, system=system, config=_config)
    try:
        yield session
    finally:
        # Could auto-save history here if configured
        pass


@asynccontextmanager
async def achat(model: Optional[str] = None, system: Optional[str] = None):
    """
    Create an async conversation context.
    
    Like chat() but for async code.
    
    Args:
        model: Specific model to use
        system: System prompt
    
    Yields:
        ChatSession that supports async calls
    
    Examples:
        >>> async with achat() as c:
        ...     response = await c.async_call("Hello!")
        ...     print(response)
    """
    session = ChatSession(model=model, system=system, config=_config)
    try:
        yield session
    finally:
        pass


def stream(prompt: str, *, model: Optional[str] = None, **kwargs) -> Generator[str, None, None]:
    """
    Stream a response token by token.
    
    This function returns a generator that yields response chunks as they
    arrive, perfect for long responses or real-time display.
    
    Args:
        prompt: Your question or request
        model: Specific model to use (optional)
        **kwargs: Additional context
    
    Yields:
        Response text chunks as they arrive
    
    Examples:
        >>> for chunk in stream("Tell me a long story"):
        ...     print(chunk, end="", flush=True)
        
        >>> # With code context
        >>> for chunk in stream("Explain this:", code=my_code):
        ...     print(chunk, end="")
    """
    # Route to appropriate model
    if model:
        model_info = _config.get_model(model)
    else:
        model_info = _router.route(prompt, hints={"streaming": True})
    
    # Create backend
    backend = create_backend(model_info.provider, model_info)
    
    # Format prompt if needed
    if kwargs:
        prompt = format_prompt_with_context(prompt, kwargs)
    
    # Stream response
    try:
        for chunk in backend.stream([{"role": "user", "content": prompt}]):
            yield chunk
    except Exception as e:
        yield f"\n[Error: {e}]"


# Async versions for modern Python code
async def ai_async(prompt: str, **kwargs) -> AgentResponse:
    """
    Async version of ai().
    
    Same parameters and behavior as ai() but runs asynchronously.
    
    Examples:
        >>> response = await ai_async("What's the weather?")
        >>> print(response)
    """
    start_time = time.time()
    
    # Extract parameters
    model = kwargs.pop("model", None)
    fast = kwargs.pop("fast", False)
    quality = kwargs.pop("quality", False)
    
    # Route to model
    hints = {"fast": fast, "quality": quality}
    if model:
        model_info = _config.get_model(model)
    else:
        model_info = _router.route(prompt, hints=hints)
    
    # Create backend
    backend = create_backend(model_info.provider, model_info)
    
    # Format prompt
    if kwargs:
        prompt = format_prompt_with_context(prompt, kwargs)
    
    try:
        # Get async response
        response_text = await backend.acomplete([{"role": "user", "content": prompt}])
        
        response = AgentResponse(
            content=response_text,
            model=model_info.name,
            time=time.time() - start_time,
            metadata={
                "provider": model_info.provider,
                "hints": hints,
                "async": True
            }
        )
        
        return response
        
    except Exception as e:
        response = AgentResponse(
            content="",
            model=model_info.name,
            time=time.time() - start_time,
            _error=e
        )
        return response


async def stream_async(prompt: str, **kwargs) -> AsyncGenerator[str, None]:
    """
    Async generator version of stream().
    
    Same parameters as stream() but yields asynchronously.
    
    Examples:
        >>> async for chunk in stream_async("Tell me a story"):
        ...     print(chunk, end="")
    """
    # Extract model parameter
    model = kwargs.pop("model", None)
    
    # Route to model
    if model:
        model_info = _config.get_model(model)
    else:
        model_info = _router.route(prompt, hints={"streaming": True})
    
    # Create backend
    backend = create_backend(model_info.provider, model_info)
    
    # Format prompt
    if kwargs:
        prompt = format_prompt_with_context(prompt, kwargs)
    
    # Stream response
    try:
        async for chunk in backend.astream([{"role": "user", "content": prompt}]):
            yield chunk
    except Exception as e:
        yield f"\n[Error: {e}]"