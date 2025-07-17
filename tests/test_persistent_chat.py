"""Tests for persistent chat functionality."""

import pytest
import json
import pickle
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import tempfile

from ai import chat, PersistentChatSession, AIResponse
from ttt.chat import PersistentChatSession as ChatClass


class TestPersistentChatSession:
    """Test the PersistentChatSession class."""

    def test_session_initialization(self):
        """Test creating a new persistent session."""
        session = PersistentChatSession(
            system="Test system prompt", model="gpt-3.5-turbo", session_id="test_123"
        )

        assert session.system == "Test system prompt"
        assert session.model == "gpt-3.5-turbo"
        assert session.metadata["session_id"] == "test_123"
        assert len(session.history) == 0
        assert "created_at" in session.metadata

    def test_auto_session_id(self):
        """Test automatic session ID generation."""
        session = PersistentChatSession()

        assert session.metadata["session_id"] is not None
        assert session.metadata["session_id"].startswith("chat_")
        assert len(session.metadata["session_id"]) > 10

    @patch("ttt.routing.router")
    def test_ask_updates_history(self, mock_router):
        """Test that ask() updates conversation history."""
        # Setup mock backend
        mock_backend = Mock()
        mock_backend.ask = AsyncMock(
            return_value=AIResponse(
                "Hello! Nice to meet you.",
                model="gpt-3.5-turbo",
                backend="cloud",
                tokens_in=10,
                tokens_out=20,
                cost=0.001,
            )
        )

        # Mock router to return our backend
        mock_router.resolve_backend.return_value = mock_backend

        # Create session with the mock backend directly
        session = PersistentChatSession(backend=mock_backend, model="gpt-3.5-turbo")
        response = session.ask("Hello, my name is Bob")

        # Check history
        assert len(session.history) == 2
        assert session.history[0]["role"] == "user"
        assert session.history[0]["content"] == "Hello, my name is Bob"
        assert "timestamp" in session.history[0]

        assert session.history[1]["role"] == "assistant"
        assert session.history[1]["content"] == "Hello! Nice to meet you."
        assert session.history[1]["model"] == "gpt-3.5-turbo"
        assert session.history[1]["tokens_in"] == 10
        assert session.history[1]["tokens_out"] == 20
        assert session.history[1]["cost"] == 0.001

    @patch("ttt.routing.router")
    def test_metadata_tracking(self, mock_router):
        """Test that metadata is properly tracked."""
        # Setup mock backend
        mock_backend = Mock()
        mock_backend.ask = AsyncMock(
            return_value=AIResponse(
                "Response", model="gpt-4", tokens_in=50, tokens_out=100, cost=0.01
            )
        )

        # Mock router to return our backend
        mock_router.resolve_backend.return_value = mock_backend

        # Create session with the mock backend directly
        session = PersistentChatSession(backend=mock_backend, model="gpt-4")

        # Make multiple requests
        session.ask("First question")
        session.ask("Second question")

        # Check metadata
        assert session.metadata["total_tokens_in"] == 100  # 50 * 2
        assert session.metadata["total_tokens_out"] == 200  # 100 * 2
        assert session.metadata["total_cost"] == 0.02  # 0.01 * 2

        # Check model usage
        assert "gpt-4" in session.metadata["model_usage"]
        assert session.metadata["model_usage"]["gpt-4"]["count"] == 2
        assert session.metadata["model_usage"]["gpt-4"]["tokens_in"] == 100
        assert session.metadata["model_usage"]["gpt-4"]["tokens_out"] == 200
        assert session.metadata["model_usage"]["gpt-4"]["cost"] == 0.02

    def test_save_json(self, tmp_path):
        """Test saving session as JSON."""
        session = PersistentChatSession(
            system="Test system", model="test-model", session_id="save_test"
        )

        # Add some history
        session.history.append(
            {
                "role": "user",
                "content": "Test message",
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Save as JSON
        save_path = tmp_path / "test_session.json"
        result_path = session.save(save_path, format="json")

        assert result_path == save_path
        assert save_path.exists()

        # Verify contents
        with open(save_path) as f:
            data = json.load(f)

        assert data["version"] == "1.0"
        assert data["system"] == "Test system"
        assert data["model"] == "test-model"
        assert len(data["history"]) == 1
        assert data["metadata"]["session_id"] == "save_test"

    def test_save_pickle(self, tmp_path):
        """Test saving session as pickle."""
        session = PersistentChatSession(system="Test system", session_id="pickle_test")

        # Save as pickle
        save_path = tmp_path / "test_session.pkl"
        result_path = session.save(save_path, format="pickle")

        assert result_path == save_path
        assert save_path.exists()

        # Verify it's a valid pickle file
        with open(save_path, "rb") as f:
            data = pickle.load(f)

        assert data["version"] == "1.0"
        assert data["metadata"]["session_id"] == "pickle_test"

    def test_load_json(self, tmp_path):
        """Test loading session from JSON."""
        # Create a session file
        session_data = {
            "version": "1.0",
            "system": "Loaded system",
            "model": "loaded-model",
            "backend": "cloud",
            "history": [
                {"role": "user", "content": "Previous message"},
                {"role": "assistant", "content": "Previous response"},
            ],
            "metadata": {
                "session_id": "loaded_session",
                "created_at": datetime.now().isoformat(),
                "total_tokens_in": 100,
                "total_tokens_out": 200,
                "total_cost": 0.05,
            },
            "kwargs": {"temperature": 0.7},
        }

        save_path = tmp_path / "load_test.json"
        with open(save_path, "w") as f:
            json.dump(session_data, f)

        # Load the session
        loaded = PersistentChatSession.load(save_path)

        assert loaded.system == "Loaded system"
        assert loaded.model == "loaded-model"
        assert len(loaded.history) == 2
        assert loaded.metadata["session_id"] == "loaded_session"
        assert loaded.metadata["total_tokens_in"] == 100
        assert loaded.kwargs["temperature"] == 0.7

    def test_load_auto_format(self, tmp_path):
        """Test auto-detecting file format on load."""
        session = PersistentChatSession(session_id="auto_test")

        # Save as JSON with .json extension
        json_path = tmp_path / "session.json"
        session.save(json_path)

        # Load without specifying format
        loaded = PersistentChatSession.load(json_path)
        assert loaded.metadata["session_id"] == "auto_test"

        # Save as pickle with .pkl extension
        pkl_path = tmp_path / "session.pkl"
        session.save(pkl_path, format="pickle")

        # Load without specifying format
        loaded = PersistentChatSession.load(pkl_path)
        assert loaded.metadata["session_id"] == "auto_test"

    def test_get_summary(self):
        """Test getting session summary."""
        session = PersistentChatSession(session_id="summary_test")

        # Add some history
        session.history.extend(
            [
                {"role": "user", "content": "Question 1"},
                {"role": "assistant", "content": "Answer 1"},
                {"role": "user", "content": "Question 2"},
                {"role": "assistant", "content": "Answer 2"},
            ]
        )

        session.metadata["total_tokens_in"] = 150
        session.metadata["total_tokens_out"] = 300
        session.metadata["total_cost"] = 0.075

        summary = session.get_summary()

        assert summary["session_id"] == "summary_test"
        assert summary["message_count"] == 4
        assert summary["user_messages"] == 2
        assert summary["assistant_messages"] == 2
        assert summary["total_tokens_in"] == 150
        assert summary["total_tokens_out"] == 300
        assert summary["total_cost"] == 0.075

    def test_export_messages_text(self):
        """Test exporting messages as text."""
        session = PersistentChatSession()
        session.history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm doing well, thanks!"},
        ]

        text = session.export_messages(format="text")
        expected = "User: Hello\n\nAssistant: Hi there!\n\nUser: How are you?\n\nAssistant: I'm doing well, thanks!"
        assert text == expected

    def test_export_messages_markdown(self):
        """Test exporting messages as markdown."""
        session = PersistentChatSession()
        session.history = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
        ]

        markdown = session.export_messages(format="markdown")
        # The markdown format includes a session header and uses ### for roles
        assert markdown.startswith("# Chat Session:")
        assert "### User" in markdown
        assert "What is Python?" in markdown
        assert "### Assistant" in markdown
        assert "Python is a programming language." in markdown

    def test_export_messages_json(self):
        """Test exporting messages as JSON."""
        session = PersistentChatSession()
        session.history = [{"role": "user", "content": "Test"}]

        json_str = session.export_messages(format="json")
        data = json.loads(json_str)
        assert isinstance(data, dict)
        assert "session_id" in data
        assert "messages" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Test"

    def test_clear_history(self):
        """Test clearing conversation history."""
        session = PersistentChatSession()
        session.history = [
            {"role": "user", "content": "Message"},
            {"role": "assistant", "content": "Response"},
        ]

        session.clear()

        assert len(session.history) == 0
        # Metadata should be preserved
        assert session.metadata["session_id"] is not None

    @patch("ttt.routing.router")
    def test_multimodal_in_persistent_session(self, mock_router):
        """Test multi-modal content in persistent sessions."""
        from ai import ImageInput

        # Setup mock
        mock_backend = Mock()
        mock_backend.ask = AsyncMock(
            return_value=AIResponse("I see an image", model="gpt-4-vision-preview")
        )
        mock_router.smart_route.return_value = (mock_backend, "gpt-4-vision-preview")
        mock_router.resolve_backend.return_value = mock_backend

        # Create session with the mocked backend
        session = PersistentChatSession(backend=mock_backend)

        # Ask with image
        response = session.ask(["What's in this image?", ImageInput("test.jpg")])

        # Check history stores the multi-modal content
        assert len(session.history) == 2
        assert isinstance(session.history[0]["content"], list)
        assert len(session.history[0]["content"]) == 2
        assert session.history[0]["content"][0] == "What's in this image?"


class TestChatContextManager:
    """Test the chat() context manager with persistence."""

    def test_chat_always_persistent(self):
        """Test that chat() always returns PersistentChatSession."""
        with chat() as session:
            assert isinstance(session, PersistentChatSession)
            assert hasattr(session, "ask")
            assert hasattr(session, "stream")
            assert hasattr(session, "save")
            assert hasattr(session, "load")

    def test_chat_with_custom_session_id(self):
        """Test chat with custom session ID."""
        with chat(session_id="custom_123") as session:
            assert session.metadata["session_id"] == "custom_123"

    def test_save_and_resume_workflow(self, tmp_path):
        """Test the save and resume workflow."""
        save_path = tmp_path / "workflow_test.json"

        # Create and save a session
        with chat(system="Test assistant") as session:
            # Mock the backend
            with patch.object(session, "backend") as mock_backend:
                mock_backend.ask = AsyncMock(
                    return_value=AIResponse("I'll remember that", model="test-model")
                )

                session.ask("Remember: The secret code is 42")
                session.save(save_path)

        # Load and continue the session
        loaded = PersistentChatSession.load(save_path)
        assert loaded.system == "Test assistant"
        assert len(loaded.history) == 2
        assert "secret code is 42" in loaded.history[0]["content"]


class TestDurationCalculation:
    """Test session duration calculation."""

    def test_duration_empty_session(self):
        """Test duration for empty session."""
        session = PersistentChatSession()
        assert session._calculate_duration() == "0m"

    def test_duration_with_timestamps(self):
        """Test duration calculation with timestamps."""
        session = PersistentChatSession()

        # Set creation time
        session.metadata["created_at"] = "2024-01-01T10:00:00"

        # Add messages with timestamps
        session.history = [
            {"role": "user", "content": "Hi", "timestamp": "2024-01-01T10:00:00"},
            {
                "role": "assistant",
                "content": "Hello",
                "timestamp": "2024-01-01T10:05:00",
            },
            {"role": "user", "content": "Bye", "timestamp": "2024-01-01T10:30:00"},
            {
                "role": "assistant",
                "content": "Goodbye",
                "timestamp": "2024-01-01T11:15:00",
            },
        ]

        duration = session._calculate_duration()
        assert duration == "1h 15m"

    def test_duration_multi_day(self):
        """Test duration calculation across days."""
        session = PersistentChatSession()

        session.metadata["created_at"] = "2024-01-01T10:00:00"
        session.history = [
            {"role": "user", "content": "Start", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "End", "timestamp": "2024-01-03T14:30:00"},
        ]

        duration = session._calculate_duration()
        assert duration == "2d 4h 30m"
