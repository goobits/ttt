"""Tests for the main API functions."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from ai.api import ask, stream, chat
from ai.chat import PersistentChatSession
from ai.models import AIResponse
from ai.backends import BaseBackend


class MockBackend(BaseBackend):
    """Mock backend for testing."""

    def __init__(self, name="mock"):
        self.name_value = name
        self._is_available = True

    @property
    def name(self):
        return self.name_value

    @property
    def is_available(self):
        return self._is_available

    @property
    def models(self):
        return ["mock-model-1", "mock-model-2"]

    async def status(self):
        return {"available": self._is_available, "name": self.name_value}

    async def ask(self, prompt, **kwargs):
        return AIResponse(
            content="Mock response",
            model="mock-model",
            backend=self.name,
            time_taken=0.1,
            tokens_in=10,
            tokens_out=20,
            cost=0.001,
        )

    async def astream(self, prompt, **kwargs):
        """Stream a response."""
        chunks = ["Mock ", "streaming ", "response"]
        for chunk in chunks:
            yield chunk


@pytest.fixture
def mock_backend():
    """Provide a mock backend."""
    return MockBackend()


class TestAsk:
    """Test the ask function."""

    @patch("ai.api.router")
    def test_ask_basic(self, mock_router):
        """Test basic ask functionality."""
        # Mock the router
        mock_backend = MagicMock()
        mock_backend.ask = AsyncMock(return_value=AIResponse("Test response"))
        mock_router.smart_route.return_value = (mock_backend, "test-model")

        response = ask("Test prompt")

        assert str(response) == "Test response"
        mock_router.smart_route.assert_called_once()
        mock_backend.ask.assert_called_once()

    @patch("ai.api.router")
    def test_ask_with_model_override(self, mock_router):
        """Test ask with explicit model override."""
        mock_backend = MagicMock()
        mock_backend.ask = AsyncMock(return_value=AIResponse("Model response"))
        mock_router.smart_route.return_value = (mock_backend, "specified-model")

        response = ask("Test question", model="specified-model")

        assert str(response) == "Model response"

        # Check that model was passed to router
        call_args = mock_router.smart_route.call_args
        assert call_args[1]["model"] == "specified-model"

    @patch("ai.api.router")
    def test_ask_with_system_prompt(self, mock_router):
        """Test ask with system prompt."""
        mock_backend = MagicMock()
        mock_backend.ask = AsyncMock(return_value=AIResponse("System response"))
        mock_router.smart_route.return_value = (mock_backend, "test-model")

        response = ask("Test prompt", system="You are helpful")

        # Check that system prompt was passed to backend
        call_args = mock_backend.ask.call_args
        assert call_args[1]["system"] == "You are helpful"


class TestStream:
    """Test the stream function."""

    @patch("ai.api.router")
    def test_stream_basic(self, mock_router):
        """Test basic streaming functionality."""
        # Mock the router and backend
        mock_backend = MagicMock()

        async def mock_astream(*args, **kwargs):
            for chunk in ["Hello", " ", "world"]:
                yield chunk

        mock_backend.astream = mock_astream
        mock_router.smart_route.return_value = (mock_backend, "test-model")

        chunks = list(stream("Test prompt"))

        assert chunks == ["Hello", " ", "world"]
        mock_router.smart_route.assert_called_once()


class TestPersistentChatSession:
    """Test the PersistentChatSession class."""

    def test_chat_session_initialization(self):
        """Test chat session initialization."""
        session = PersistentChatSession(system="You are helpful", model="test-model")

        assert session.system == "You are helpful"
        assert session.model == "test-model"
        assert session.history == []

    def test_chat_session_clear(self):
        """Test clearing chat history."""
        session = PersistentChatSession()
        session.history = [{"role": "user", "content": "test"}]

        session.clear()

        assert session.history == []


class TestChatContextManager:
    """Test the chat context manager."""

    def test_chat_context_manager(self):
        """Test using chat as context manager."""
        with chat(system="Be helpful") as session:
            assert session.system == "Be helpful"
            assert isinstance(session, PersistentChatSession)
