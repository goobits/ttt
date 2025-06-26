"""Tests for the main API functions."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from ai.api import ask, stream, chat, ChatSession
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
    def test_ask_with_preferences(self, mock_router):
        """Test ask with speed/quality preferences."""
        mock_backend = MagicMock()
        mock_backend.ask = AsyncMock(return_value=AIResponse("Fast response"))
        mock_router.smart_route.return_value = (mock_backend, "fast-model")

        response = ask("Quick question", fast=True)

        assert str(response) == "Fast response"

        # Check that preferences were passed to router
        call_args = mock_router.smart_route.call_args
        assert call_args[1]["prefer_speed"] is True

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


class TestChatSession:
    """Test the ChatSession class."""

    @patch("ai.api._get_default_backend")
    def test_chat_session_initialization(self, mock_get_default, mock_backend):
        """Test chat session initialization."""
        mock_get_default.return_value = mock_backend

        session = ChatSession(system="You are helpful", model="test-model")

        assert session.system == "You are helpful"
        assert session.model == "test-model"
        assert session.history == []

    @patch("ai.api._get_default_backend")
    def test_chat_session_ask(self, mock_get_default, mock_backend):
        """Test asking in a chat session."""
        mock_get_default.return_value = mock_backend

        session = ChatSession()
        response = session.ask("Hello")

        assert str(response) == "Mock response"
        assert len(session.history) == 2  # User message + assistant response
        assert session.history[0]["role"] == "user"
        assert session.history[0]["content"] == "Hello"
        assert session.history[1]["role"] == "assistant"
        assert session.history[1]["content"] == "Mock response"

    @patch("ai.api._get_default_backend")
    def test_chat_session_conversation(self, mock_get_default, mock_backend):
        """Test multi-turn conversation."""
        mock_backend.ask = AsyncMock(
            side_effect=[
                AIResponse("I'm fine, thanks!"),
                AIResponse("Nice to meet you!"),
            ]
        )
        mock_get_default.return_value = mock_backend

        session = ChatSession()

        # First message
        response1 = session.ask("How are you?")
        assert str(response1) == "I'm fine, thanks!"

        # Second message - should include conversation history
        response2 = session.ask("I'm Alice")
        assert str(response2) == "Nice to meet you!"

        # Check that conversation history was built
        second_call_args = mock_backend.ask.call_args_list[1]
        prompt = second_call_args[0][0]  # First positional argument

        # Should contain previous conversation
        assert "How are you?" in prompt
        assert "I'm fine, thanks!" in prompt
        assert "I'm Alice" in prompt

    @patch("ai.api._get_default_backend")
    def test_chat_session_clear(self, mock_get_default, mock_backend):
        """Test clearing chat history."""
        mock_get_default.return_value = mock_backend

        session = ChatSession()
        session.history = [{"role": "user", "content": "test"}]

        session.clear()

        assert session.history == []


class TestChatContextManager:
    """Test the chat context manager."""

    @patch("ai.api._get_default_backend")
    def test_chat_context_manager(self, mock_get_default, mock_backend):
        """Test using chat as context manager."""
        mock_get_default.return_value = mock_backend

        with chat(system="Be helpful") as session:
            response = session.ask("Hi")
            assert str(response) == "Mock response"
            assert session.system == "Be helpful"
