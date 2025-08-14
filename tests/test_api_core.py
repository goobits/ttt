"""Tests for the main API functions."""

import pytest

from ttt import AIResponse, chat
from ttt.session.chat import PersistentChatSession
from tests.utils import MockBackend




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


# TestChatContextManager removed to eliminate duplication
# Comprehensive chat context manager tests are in test_chat.py
