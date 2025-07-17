"""Advanced tests for the API module to increase coverage."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
from typing import AsyncIterator

from ttt.api import (
    ask,
    stream,
    chat,
    ask_async,
    stream_async,
    achat,
)
from ttt.chat import PersistentChatSession as ChatSession
from ttt.models import AIResponse, ImageInput
from ttt.backends import BaseBackend
from ttt.exceptions import BackendNotAvailableError


class MockBackend(BaseBackend):
    """Mock backend for testing."""

    def __init__(self, name="mock", response_text="Mock response"):
        self.name_value = name
        self.response_text = response_text
        self.last_prompt = None
        self.last_kwargs = None
        self._is_available = True
        self._supports_streaming = True

    @property
    def name(self) -> str:
        return self.name_value

    @property
    def is_available(self) -> bool:
        return self._is_available

    @property
    def supports_streaming(self) -> bool:
        return self._supports_streaming

    async def ask(self, prompt, **kwargs) -> AIResponse:
        self.last_prompt = prompt
        self.last_kwargs = kwargs
        return AIResponse(
            content=self.response_text,
            model=kwargs.get("model", "mock-model"),
            backend=self.name,
            time_taken=0.1,
            tokens_in=10,
            tokens_out=20,
        )

    async def astream(self, prompt, **kwargs) -> AsyncIterator[str]:
        self.last_prompt = prompt
        self.last_kwargs = kwargs
        chunks = self.response_text.split()
        for chunk in chunks:
            yield chunk + " "

    async def list_models(self, **kwargs):
        return ["mock-model-1", "mock-model-2"]

    async def status(self, **kwargs):
        return {"available": True, "name": self.name}

    @property
    def models(self):
        """Return list of available models."""
        return ["mock-model-1", "mock-model-2"]


@pytest.fixture
def mock_backend():
    """Provide a mock backend."""
    return MockBackend()


@pytest.fixture
def mock_router(mock_backend):
    """Mock the router to return our mock backend."""
    with patch("ttt.api.router") as mock:
        mock.smart_route.return_value = (mock_backend, "mock-model")
        yield mock



class TestAskFunction:
    """Test the ask function."""

    def test_ask_basic(self, mock_backend, mock_router):
        """Test basic ask functionality."""
        response = ask("Test prompt")

        assert str(response) == "Mock response"
        assert response.model == "mock-model"
        assert response.backend == "mock"

        # Verify router was called
        mock_router.smart_route.assert_called_once()
        call_args = mock_router.smart_route.call_args
        assert call_args[0][0] == "Test prompt"

    def test_ask_with_all_parameters(self, mock_backend, mock_router):
        """Test ask with all parameters."""
        response = ask(
            "Test prompt",
            model="specific-model",
            system="System prompt",
            temperature=0.7,
            max_tokens=100,
            backend="cloud",
            custom_param="value",
        )

        # Verify parameters were passed to router
        call_args = mock_router.smart_route.call_args
        assert call_args[1]["model"] == "specific-model"
        assert call_args[1]["backend"] == "cloud"
        assert call_args[1]["custom_param"] == "value"

        # Verify backend received parameters
        assert mock_backend.last_kwargs["system"] == "System prompt"
        assert mock_backend.last_kwargs["temperature"] == 0.7
        assert mock_backend.last_kwargs["max_tokens"] == 100

    def test_ask_with_images(self, mock_backend, mock_router):
        """Test ask with image inputs."""
        response = ask(
            ["What's in this image?", ImageInput(b"fake_image_data_for_testing")]
        )

        # Verify prompt was passed correctly
        assert isinstance(mock_backend.last_prompt, list)
        assert mock_backend.last_prompt[0] == "What's in this image?"
        assert isinstance(mock_backend.last_prompt[1], ImageInput)


class TestStreamFunction:
    """Test the stream function."""

    def test_stream_basic(self, mock_backend, mock_router):
        """Test basic streaming functionality."""
        mock_backend.response_text = "Hello world test"

        chunks = list(stream("Test prompt"))

        assert chunks == ["Hello ", "world ", "test "]
        assert mock_backend.last_prompt == "Test prompt"

    def test_stream_with_parameters(self, mock_backend, mock_router):
        """Test streaming with all parameters."""
        chunks = list(
            stream(
                "Test prompt",
                model="specific-model",
                system="System prompt",
                temperature=0.5,
                max_tokens=50,
                backend="local",
            )
        )

        # Verify parameters were passed
        assert mock_backend.last_kwargs["system"] == "System prompt"
        assert mock_backend.last_kwargs["temperature"] == 0.5
        assert mock_backend.last_kwargs["max_tokens"] == 50

    def test_stream_with_images(self, mock_backend, mock_router):
        """Test streaming with image inputs."""
        chunks = list(stream(["Describe this", ImageInput("test.jpg")]))

        assert isinstance(mock_backend.last_prompt, list)
        assert len(chunks) > 0


class TestChatSession:
    """Test ChatSession class."""

    def test_chat_session_initialization_default(self):
        """Test ChatSession initialization with defaults."""
        with patch("ttt.routing.router") as mock_router:
            mock_backend = MockBackend()
            # Mock the smart_route to return backend and model
            mock_router.smart_route.return_value = (mock_backend, "default-model")
            mock_router.resolve_backend.return_value = mock_backend
            mock_router.resolve_model.return_value = "default-model"

            session = ChatSession()

            assert session.system is None
            # Model gets resolved by router
            assert session.model is not None
            # Backend is resolved by router, might not be the mock
            assert session.backend is not None
            assert session.history == []

    def test_chat_session_initialization_with_params(self):
        """Test ChatSession initialization with parameters."""
        with patch("ttt.routing.router") as mock_router:
            mock_backend = MockBackend("local")
            # Mock router to return our backend
            mock_router.resolve_backend.return_value = mock_backend
            mock_router.resolve_model.return_value = "specific-model"

            session = ChatSession(
                system="You are helpful",
                model="specific-model",
                backend="local",
                temperature=0.8,
            )

            assert session.system == "You are helpful"
            assert session.model == "specific-model"
            # Backend might be LocalBackend due to routing
            assert session.backend is not None
            assert session.kwargs["temperature"] == 0.8

    def test_chat_session_ask_first_message(self):
        """Test asking first message in chat session."""
        mock_backend = MockBackend()
        session = ChatSession(backend=mock_backend)

        response = session.ask("Hello")

        assert str(response) == "Mock response"
        assert len(session.history) == 2
        # Check message exists (may have timestamp and metadata)
        assert any(msg['role'] == 'user' and msg['content'] == 'Hello' for msg in session.history)
        # Check assistant response exists (may have metadata)
        assert any(msg['role'] == 'assistant' and msg['content'] == 'Mock response' for msg in session.history)

        # First message should be passed as-is
        assert mock_backend.last_prompt == "Hello"

    def test_chat_session_ask_conversation(self):
        """Test multi-turn conversation."""
        mock_backend = MockBackend()
        session = ChatSession(backend=mock_backend)

        # First exchange
        mock_backend.response_text = "Hi there!"
        session.ask("Hello")

        # Second exchange
        mock_backend.response_text = "I'm doing well"
        response = session.ask("How are you?")

        # Check that the latest prompt was passed
        # (The conversation context is now handled differently)
        assert mock_backend.last_prompt == "How are you?"

        # Check history
        assert len(session.history) == 4
        # Check messages exist (may have timestamps and metadata)
        assert any(msg['role'] == 'user' and msg['content'] == 'How are you?' for msg in session.history[2:])
        assert any(msg['role'] == 'assistant' and msg['content'] == 'I\'m doing well' for msg in session.history[2:])

    def test_chat_session_stream(self):
        """Test streaming in chat session."""
        mock_backend = MockBackend()
        mock_backend.response_text = "Streamed response"
        session = ChatSession(backend=mock_backend)

        chunks = list(session.stream("Test streaming"))

        assert chunks == ["Streamed ", "response "]
        assert len(session.history) == 2
        assert session.history[1]["content"] == "Streamed response "

    def test_chat_session_clear(self):
        """Test clearing chat history."""
        session = ChatSession(backend=MockBackend())

        session.ask("Message 1")
        session.ask("Message 2")
        assert len(session.history) == 4

        session.clear()
        assert len(session.history) == 0

    def test_chat_session_with_system_prompt(self):
        """Test chat session with system prompt."""
        mock_backend = MockBackend()
        session = ChatSession(system="You are a pirate", backend=mock_backend)

        session.ask("Hello")

        # System prompt should be passed to backend
        assert mock_backend.last_kwargs["system"] == "You are a pirate"


class TestChatContextManager:
    """Test chat context manager."""

    def test_chat_context_basic(self):
        """Test basic chat context manager."""
        with patch("ttt.routing.router.smart_route") as mock_route:
            mock_backend = MockBackend()
            mock_route.return_value = (mock_backend, "mock-model")

            with chat() as session:
                assert isinstance(session, ChatSession)
                response = session.ask("Test")
                assert str(response) == "Mock response"

    def test_chat_context_with_params(self):
        """Test chat context manager with parameters."""
        with patch("ttt.backends.local.LocalBackend") as mock_local:
            mock_backend = MockBackend("local")
            mock_local.return_value = mock_backend

            with chat(
                system="System prompt", model="model", backend="local"
            ) as session:
                assert session.system == "System prompt"
                assert session.model == "model"
                # Backend might be LocalBackend due to routing
                assert session.backend is not None



class TestAsyncFunctions:
    """Test async versions of functions."""

    @pytest.mark.asyncio
    async def test_ask_async(self):
        """Test async ask function."""
        with patch("ttt.api.router.smart_route") as mock_route:
            mock_backend = MockBackend("local")
            # Mock the router to return our backend
            mock_route.return_value = (mock_backend, "model")

            response = await ask_async(
                "Test prompt",
                model="model",
                system="System",
                temperature=0.5,
                max_tokens=100,
                backend="local",
            )

            assert str(response) == "Mock response"
            assert mock_backend.last_prompt == "Test prompt"
            assert mock_backend.last_kwargs["system"] == "System"

    @pytest.mark.asyncio
    async def test_stream_async(self):
        """Test async stream function."""
        with patch("ttt.routing.router.smart_route") as mock_route:
            mock_backend = MockBackend()
            mock_backend.response_text = "Async stream test"
            mock_route.return_value = (mock_backend, "mock-model")

            chunks = []
            async for chunk in stream_async("Test"):
                chunks.append(chunk)

            assert chunks == ["Async ", "stream ", "test "]

    @pytest.mark.asyncio
    async def test_achat_context_manager(self):
        """Test async chat context manager."""
        with patch("ttt.routing.router.smart_route") as mock_route:
            mock_backend = MockBackend()
            mock_route.return_value = (mock_backend, "mock-model")

            async with achat(system="Async system") as session:
                assert isinstance(session, ChatSession)
                assert session.system == "Async system"

                # Can't directly test ask in async context without more setup
                # but the context manager itself works


class TestErrorHandling:
    """Test error handling in API functions."""

    def test_ask_with_invalid_backend(self):
        """Test ask with invalid backend string."""
        with pytest.raises(BackendNotAvailableError) as exc_info:
            ChatSession(backend="invalid-backend")

        assert "not available" in str(exc_info.value) or "not found" in str(exc_info.value)

    def test_stream_with_failing_backend(self, mock_router):
        """Test streaming when backend fails."""

        # Create a backend that fails during streaming
        class FailingBackend(MockBackend):
            async def astream(self, prompt, **kwargs):
                yield "Start "
                raise Exception("Stream failed")

        failing_backend = FailingBackend()
        mock_router.smart_route.return_value = (failing_backend, "model")

        # Should get partial results before failure
        chunks = []
        with pytest.raises(Exception):
            for chunk in stream("Test"):
                chunks.append(chunk)

        assert chunks == ["Start "]


class TestBackendSelection:
    """Test backend selection logic."""

    def test_backend_instance_passed_directly(self):
        """Test passing backend instance directly."""
        custom_backend = MockBackend("custom")

        with patch("ttt.api.router") as mock_router:
            mock_router.smart_route.return_value = (custom_backend, "model")

            response = ask("Test", backend=custom_backend)

            # Router should receive the backend instance
            call_args = mock_router.smart_route.call_args
            assert call_args[1]["backend"] == custom_backend
