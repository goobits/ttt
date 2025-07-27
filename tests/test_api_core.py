"""Tests for the main API functions."""

import pytest

from ttt import AIResponse, chat
from ttt.backends import BaseBackend
from ttt.session.chat import PersistentChatSession


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


# Removed overly mocked tests that don't test real behavior
# These tests were mocking the entire router, essentially testing that mocks work
# rather than testing actual API functionality


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
