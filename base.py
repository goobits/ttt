#!/usr/bin/env python3
"""
Agent abstraction layer for multi-agent workflows.

This module provides a flexible base class for different AI agents,
allowing easy swapping of providers and implementations.
"""

import asyncio
import time
import threading
import queue
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Generator
from litellm import completion, acompletion
import os


@dataclass
class AgentResponse:
    """Structured response from an agent including content and metadata."""

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    """Abstract base class for all agents in the multi-agent system."""

    @abstractmethod
    def get_response(self, prompt: str, **kwargs) -> AgentResponse:
        """
        Get a response from the agent for the given prompt.

        Args:
            prompt: The prompt to send to the agent
            **kwargs: Additional agent-specific parameters

        Returns:
            An AgentResponse containing the content and metadata
        """
        pass

    @abstractmethod
    async def get_response_async(self, prompt: str, **kwargs) -> AgentResponse:
        """
        Asynchronously get a response from the agent for the given prompt.

        Args:
            prompt: The prompt to send to the agent
            **kwargs: Additional agent-specific parameters

        Returns:
            An AgentResponse containing the content and metadata
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the name/identifier of this agent."""
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this agent (optional override)."""
        return {}

    def supports_streaming(self) -> bool:
        """Check if this agent can stream responses."""
        return False

    def get_response_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """
        Yields response chunks as they are generated.
        Default implementation for non-streaming agents.
        """
        response = self.get_response(prompt, **kwargs)
        yield response.content

    def get_response_string(self, prompt: str, **kwargs) -> str:
        """
        Compatibility method that returns just the response string.

        Args:
            prompt: The prompt to send to the agent
            **kwargs: Additional agent-specific parameters

        Returns:
            The agent's response as a string
        """
        return self.get_response(prompt, **kwargs).content


class OpenRouterAgent(Agent):
    """Agent that uses LiteLLM to access various LLM providers via OpenRouter."""

    def __init__(self, model: str, system_message: Optional[str] = None):
        """
        Initialize an OpenRouter agent.

        Args:
            model: The model identifier (e.g., 'google/gemini-2.0-flash-exp')
            system_message: Optional system message for the agent
        """
        self.model = model
        self.system_message = system_message
        self.api_key = os.getenv("OPENROUTER_API_KEY")

    def get_response(self, prompt: str, **kwargs) -> AgentResponse:
        """Get response from OpenRouter via LiteLLM."""
        start_time = time.time()

        # Use the model specified, with any override from kwargs
        model = kwargs.get("model", self.model)

        # Ensure model has openrouter/ prefix for LiteLLM
        if not model.startswith("openrouter/"):
            model = f"openrouter/{model}"

        # Build messages list
        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            response_obj = completion(
                model=model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000),
                api_key=self.api_key,
            )

            content = response_obj.choices[0].message.content
            metadata = {
                "response_time": time.time() - start_time,
                "agent_type": self.__class__.__name__,
                "model": model,
                "tokens_used": getattr(response_obj.usage, "total_tokens", None),
                "prompt_tokens": getattr(response_obj.usage, "prompt_tokens", None),
                "completion_tokens": getattr(
                    response_obj.usage, "completion_tokens", None
                ),
                "finish_reason": response_obj.choices[0].finish_reason,
            }

            return AgentResponse(content=content, metadata=metadata)
        except Exception as e:
            return AgentResponse(
                content=f"LiteLLM OpenRouter error: {e}",
                metadata={"error": str(e), "response_time": time.time() - start_time},
            )

    async def get_response_async(self, prompt: str, **kwargs) -> AgentResponse:
        """Get response asynchronously from OpenRouter via LiteLLM."""
        start_time = time.time()

        model = kwargs.get("model", self.model)
        if not model.startswith("openrouter/"):
            model = f"openrouter/{model}"

        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            # Use the async completion function
            response_obj = await acompletion(
                model=model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000),
                api_key=self.api_key,
            )

            content = response_obj.choices[0].message.content
            metadata = {
                "response_time": time.time() - start_time,
                "agent_type": self.__class__.__name__,
                "model": model,
                "tokens_used": getattr(response_obj.usage, "total_tokens", None),
                "prompt_tokens": getattr(response_obj.usage, "prompt_tokens", None),
                "completion_tokens": getattr(
                    response_obj.usage, "completion_tokens", None
                ),
                "finish_reason": response_obj.choices[0].finish_reason,
                "async": True,
            }

            return AgentResponse(content=content, metadata=metadata)
        except Exception as e:
            return AgentResponse(
                content=f"LiteLLM OpenRouter async error: {e}",
                metadata={
                    "error": str(e),
                    "response_time": time.time() - start_time,
                    "async": True,
                },
            )

    def get_name(self) -> str:
        """Return the model name as the agent identifier."""
        return self.model

    def get_capabilities(self) -> Dict[str, Any]:
        """Return capabilities based on the model."""
        return {
            "supports_json": True,
            "supports_streaming": True,
            "max_tokens": 4096,  # This could be model-specific
            "provider": "openrouter (via LiteLLM)",
        }

    def supports_streaming(self) -> bool:
        """OpenRouter supports streaming through LiteLLM."""
        return True

    def get_response_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Stream the response from OpenRouter."""
        model = kwargs.get("model", self.model)
        if not model.startswith("openrouter/"):
            model = f"openrouter/{model}"

        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            # Set stream=True for streaming response
            response_stream = completion(
                model=model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000),
                api_key=self.api_key,
                stream=True,
            )

            for chunk in response_stream:
                # Extract content from the chunk
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            yield f"LiteLLM streaming error: {e}"


class ClaudeCLIAgent(Agent):
    """Agent that interacts with Claude through the CLI interface."""

    def __init__(self, text_injector=None, monitor=None):
        """
        Initialize a Claude CLI agent.

        Args:
            text_injector: TextInjector instance for sending commands
            monitor: EventDrivenClaudeMonitor instance for state tracking
        """
        self.text_injector = text_injector
        self.monitor = monitor
        self._response_buffer = []
        self._response_complete = False
        self._completion_event = threading.Event()
        self._completion_detected = False
        self._stream_queue = queue.Queue()
        # Thread safety lock for shared state
        self._lock = threading.Lock()

        # Event listener setup skipped - monitor not available

    def get_response(self, prompt: str, **kwargs) -> AgentResponse:
        """
        Send prompt to Claude CLI and collect response.

        Args:
            prompt: The prompt to send to Claude
            timeout: Optional timeout in seconds (default: 300)

        Returns:
            An AgentResponse containing the content and metadata
        """
        if not self.text_injector:
            raise RuntimeError("ClaudeCLIAgent requires a text_injector")

        start_time = time.time()
        timeout = kwargs.get("timeout", 300)  # 5 minutes default

        # Clear previous response and stream queue
        with self._lock:
            self._response_buffer.clear()
            self._response_complete = False
            self._completion_detected = False
        self._completion_event.clear()
        # Clear stream queue atomically
        with self._lock:
            while not self._stream_queue.empty():
                try:
                    self._stream_queue.get_nowait()
                except queue.Empty:
                    break

        # Inject the prompt
        self.text_injector.inject_text(prompt)

        # Wait for completion with timeout
        if self._completion_event.wait(timeout):
            # Capture the complete response
            with self._lock:
                response_content = "\n".join(self._response_buffer)
                self._response_complete = True

            metadata = {
                "response_time": time.time() - start_time,
                "agent_type": self.__class__.__name__,
                "timeout_used": timeout,
                "completion_detected": self._completion_detected,
            }

            return AgentResponse(content=response_content, metadata=metadata)
        else:
            raise TimeoutError(f"Claude CLI response timed out after {timeout} seconds")

    async def get_response_async(self, prompt: str, **kwargs) -> AgentResponse:
        """Run the synchronous get_response in a separate thread."""
        return await asyncio.to_thread(self.get_response, prompt, **kwargs)

    def get_name(self) -> str:
        """Return identifier for Claude CLI."""
        return "claude-cli"

    def get_capabilities(self) -> Dict[str, Any]:
        """Return Claude CLI capabilities."""
        return {
            "supports_json": False,  # CLI doesn't guarantee JSON
            "supports_streaming": True,
            "supports_tools": True,
            "supports_compact": True,
            "provider": "anthropic-cli",
        }

    def supports_streaming(self) -> bool:
        """Claude CLI supports streaming through event monitoring."""
        return True

    def get_response_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Stream the response from the Claude CLI."""
        if not self.text_injector:
            raise RuntimeError("ClaudeCLIAgent requires a text_injector")

        # Clear stream queue first
        with self._lock:
            while not self._stream_queue.empty():
                try:
                    self._stream_queue.get_nowait()
                except queue.Empty:
                    break

        # Start response collection in background thread
        # This allows us to yield chunks immediately as they arrive
        def inject_prompt():
            with self._lock:
                self._response_buffer.clear()
                self._response_complete = False
                self._completion_detected = False
            self._completion_event.clear()
            self.text_injector.inject_text(prompt)

        # Start injection in background
        inject_thread = threading.Thread(target=inject_prompt)
        inject_thread.start()

        # Yield chunks as they arrive
        while True:
            try:
                # Wait for chunk with timeout
                chunk = self._stream_queue.get(timeout=1.0)
                if chunk is None:  # End of stream
                    break
                yield chunk
            except queue.Empty:
                # Check if thread is still running
                if not inject_thread.is_alive() and self._stream_queue.empty():
                    break

        inject_thread.join()  # Ensure thread completes


class MockAgent(Agent):
    """Mock agent for testing purposes."""

    def __init__(
        self, name: str = "mock-agent", responses: Optional[Dict[str, str]] = None
    ):
        """
        Initialize a mock agent.

        Args:
            name: Name for this mock agent
            responses: Dict mapping prompts (or parts of prompts) to responses
        """
        self.name = name
        self.responses = responses or {}
        self.default_response = "Mock response"
        self.call_history = []

    def get_response(self, prompt: str, **kwargs) -> AgentResponse:
        """Return a mock response based on the prompt."""
        start_time = time.time()
        self.call_history.append({"prompt": prompt, "kwargs": kwargs})

        # Check if we have a specific response for this prompt
        content = self.default_response
        for key, response in self.responses.items():
            if key in prompt:
                content = response
                break

        metadata = {
            "response_time": 0.001,  # Mock response is instant
            "agent_type": self.__class__.__name__,
            "mock": True,
        }

        return AgentResponse(content=content, metadata=metadata)

    async def get_response_async(self, prompt: str, **kwargs) -> AgentResponse:
        """Return a mock response asynchronously."""
        self.call_history.append({"prompt": prompt, "kwargs": kwargs, "async": True})

        # Simulate some async delay
        await asyncio.sleep(0.001)

        # Check for a specific response
        content = self.default_response
        for key, response in self.responses.items():
            if key in prompt:
                content = response
                break

        metadata = {
            "response_time": 0.001,
            "agent_type": self.__class__.__name__,
            "mock": True,
            "async": True,
        }

        return AgentResponse(content=content, metadata=metadata)

    def get_name(self) -> str:
        """Return the mock agent's name."""
        return self.name

    def get_call_history(self) -> list:
        """Get the history of calls made to this agent."""
        return self.call_history.copy()


# Factory function for creating agents
def create_agent(agent_type: str, **kwargs) -> Agent:
    """
    Factory function to create agents of different types.

    Args:
        agent_type: Type of agent ('openrouter', 'claude-cli', 'mock')
        **kwargs: Agent-specific configuration

    Returns:
        An Agent instance

    Raises:
        ValueError: If agent_type is not recognized
    """
    if agent_type == "openrouter":
        return OpenRouterAgent(**kwargs)
    elif agent_type == "claude-cli":
        return ClaudeCLIAgent(**kwargs)
    elif agent_type == "mock":
        return MockAgent(**kwargs)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
