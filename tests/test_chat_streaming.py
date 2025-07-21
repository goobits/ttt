"""Advanced tests for the chat module to increase coverage."""

import json
import pickle
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from ttt.backends import BaseBackend
from ttt.chat import PersistentChatSession, _estimate_tokens
from ttt.exceptions import (
    InvalidParameterError,
    SessionLoadError,
    SessionSaveError,
)
from ttt.models import AIResponse, ImageInput


class MockBackend(BaseBackend):
    """Mock backend for testing."""

    def __init__(self, name="mock"):
        self.name_value = name
        self._is_available = True
        self.responses = ["Response 1", "Response 2", "Response 3"]
        self.response_index = 0

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
        response = self.responses[self.response_index % len(self.responses)]
        self.response_index += 1

        # Handle both string and list prompts
        if isinstance(prompt, list):
            # Extract text content from list
            text_parts = [item for item in prompt if isinstance(item, str)]
            prompt_text = " ".join(text_parts)
        else:
            prompt_text = prompt

        return AIResponse(
            content=response,
            model=kwargs.get("model", "mock-model"),
            backend=self.name,
            time_taken=0.1,
            tokens_in=len(prompt_text.split()) * 2,
            tokens_out=len(response.split()) * 2,
            cost=0.001,
        )

    async def astream(self, prompt, **kwargs):
        """Stream a response."""
        response = self.responses[self.response_index % len(self.responses)]
        self.response_index += 1

        for chunk in response.split():
            yield chunk + " "


@pytest.fixture
def mock_backend():
    """Provide a mock backend."""
    return MockBackend()


@pytest.fixture
def mock_router(mock_backend):
    """Mock router to return our backend."""
    with patch("ttt.routing.router") as mock:
        mock.smart_route.return_value = (mock_backend, "mock-model")
        mock.resolve_backend.return_value = mock_backend
        mock.resolve_model.return_value = "mock-model"
        yield mock


class TestPersistentChatSessionAdvanced:
    """Advanced tests for PersistentChatSession."""

    def test_init_with_all_parameters(self, mock_router, mock_backend):
        """Test initialization with all parameters."""
        session = PersistentChatSession(
            system="Custom system prompt",
            model="specific-model",
            backend=mock_backend,
            session_id="custom-id",
            temperature=0.7,
        )

        assert session.system == "Custom system prompt"
        assert session.model == "specific-model"
        assert session.metadata["session_id"] == "custom-id"
        assert session.kwargs["temperature"] == 0.7
        assert session.history == []
        assert "created_at" in session.metadata

    def test_auto_generate_session_id(self, mock_router):
        """Test automatic session ID generation."""
        # Need to patch the _generate_session_id method directly
        with patch.object(
            PersistentChatSession, "_generate_session_id"
        ) as mock_generate:
            mock_generate.return_value = "chat_20240101_120000_abcd1234"

            session = PersistentChatSession()

            assert session.metadata["session_id"] == "chat_20240101_120000_abcd1234"

    def test_ask_with_multimodal_content(self, mock_router, mock_backend):
        """Test asking with multimodal content."""
        session = PersistentChatSession(backend=mock_backend)

        response = session.ask(["What's in this image?", ImageInput("test.jpg")])

        assert str(response) == "Response 1"
        assert len(session.history) == 2

        # Check message storage
        user_msg = session.history[0]
        assert user_msg["role"] == "user"
        assert isinstance(user_msg["content"], list)
        assert user_msg["content"][0] == "What's in this image?"

    def test_metadata_tracking_comprehensive(self, mock_router, mock_backend):
        """Test comprehensive metadata tracking."""
        session = PersistentChatSession(model="test-model", backend=mock_backend)

        # Make several asks to accumulate metadata
        session.ask("First question")
        session.ask("Second question", model="different-model")
        session.ask("Third question")

        metadata = session.metadata

        # Check token counts
        assert metadata["total_tokens_in"] > 0
        assert metadata["total_tokens_out"] > 0
        assert metadata["total_cost"] > 0

        # Check model usage
        assert "test-model" in metadata["model_usage"]
        assert "different-model" in metadata["model_usage"]
        assert metadata["model_usage"]["test-model"]["count"] == 2
        assert metadata["model_usage"]["different-model"]["count"] == 1

        # Check backend usage
        assert "mock" in metadata["backend_usage"]
        assert metadata["backend_usage"]["mock"]["count"] == 3

    def test_save_json_comprehensive(self, mock_router):
        """Test comprehensive JSON save functionality."""
        session = PersistentChatSession(
            system="Test system", model="test-model", session_id="test-session"
        )

        # Add messages with different types
        session.history = [
            {
                "role": "user",
                "content": "Text message",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "role": "assistant",
                "content": "Response",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": "test-model",
                "tokens": {"in": 10, "out": 20},
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            session.save(temp_path)

            # Verify saved content
            with open(temp_path) as f:
                saved_data = json.load(f)

            assert saved_data["version"] == "1.0"
            assert saved_data["session_id"] == "test-session"
            assert saved_data["system"] == "Test system"
            assert saved_data["model"] == "test-model"
            assert len(saved_data["messages"]) == 2
            assert "metadata" in saved_data
            assert saved_data["metadata"]["message_count"] == 2

        finally:
            temp_path.unlink()

    def test_save_pickle_format(self, mock_router, mock_backend):
        """Test saving in pickle format."""
        session = PersistentChatSession(backend=mock_backend)
        session.ask("Test message")

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            temp_path = Path(f.name)

        try:
            session.save(temp_path, format="pickle")

            # Verify pickle file was created
            with open(temp_path, "rb") as f:
                loaded_data = pickle.load(f)

            assert loaded_data["session_id"] == session.metadata["session_id"]
            assert len(loaded_data["messages"]) == 2

        finally:
            temp_path.unlink()

    def test_save_invalid_format(self, mock_router, mock_backend):
        """Test saving with invalid format."""
        session = PersistentChatSession(backend=mock_backend)

        with pytest.raises(InvalidParameterError) as exc_info:
            session.save("test.xml", format="xml")

        assert exc_info.value.details["parameter"] == "format"
        assert exc_info.value.details["value"] == "xml"

    def test_save_permission_error(self, mock_router, mock_backend):
        """Test handling permission errors during save."""
        session = PersistentChatSession(backend=mock_backend)

        # Try to save to a path that will fail
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(SessionSaveError) as exc_info:
                session.save("/root/test.json")

        assert "Access denied" in str(exc_info.value)

    def test_load_json_comprehensive(self, mock_router, mock_backend):
        """Test comprehensive JSON loading."""
        # Create test data
        test_data = {
            "version": "1.0",
            "session_id": "loaded-session",
            "system": "Loaded system",
            "model": "loaded-model",
            "messages": [
                {
                    "role": "user",
                    "content": "Loaded message",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "metadata": {
                "start_time": datetime.now(timezone.utc).isoformat(),
                "message_count": 1,
                "total_tokens_in": 10,
                "total_tokens_out": 20,
                "total_cost": 0.001,
            },
            "kwargs": {"temperature": 0.8},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            loaded_session = PersistentChatSession.load(temp_path)

            assert loaded_session.metadata["session_id"] == "loaded-session"
            assert loaded_session.system == "Loaded system"
            assert loaded_session.model == "loaded-model"
            assert len(loaded_session.history) == 1
            assert loaded_session.kwargs["temperature"] == 0.8
            assert loaded_session.metadata["total_tokens_in"] == 10

        finally:
            temp_path.unlink()

    def test_load_pickle_format(self, mock_router, mock_backend):
        """Test loading pickle format."""
        # Create and save a session in pickle format
        original = PersistentChatSession(session_id="pickle-test", backend=mock_backend)
        original.history = [{"role": "user", "content": "Pickle test"}]

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            temp_path = Path(f.name)

        try:
            original.save(temp_path, format="pickle")

            # Load it back
            loaded = PersistentChatSession.load(temp_path, format="pickle")

            assert loaded.session_id == "pickle-test"
            assert len(loaded.messages) == 1
            assert loaded.messages[0]["content"] == "Pickle test"

        finally:
            temp_path.unlink()

    def test_load_auto_format_detection(self, mock_router, mock_backend):
        """Test automatic format detection during load."""
        session = PersistentChatSession(backend=mock_backend)

        # Test JSON detection
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            session.save(f.name)
            loaded = PersistentChatSession.load(f.name)  # Auto-detect JSON
            assert loaded.metadata["session_id"] == session.metadata["session_id"]
            Path(f.name).unlink()

        # Test pickle detection
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            session.save(f.name, format="pickle")
            loaded = PersistentChatSession.load(f.name)  # Auto-detect pickle
            assert loaded.metadata["session_id"] == session.metadata["session_id"]
            Path(f.name).unlink()

    def test_load_corrupted_json(self, mock_router):
        """Test loading corrupted JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json}")
            temp_path = Path(f.name)

        try:
            with pytest.raises(SessionLoadError) as exc_info:
                PersistentChatSession.load(temp_path)

            assert "Invalid JSON" in str(exc_info.value)

        finally:
            temp_path.unlink()

    def test_get_summary(self, mock_router, mock_backend):
        """Test getting session summary."""
        session = PersistentChatSession(backend=mock_backend)

        # Add some activity
        session.ask("Question 1")
        session.ask("Question 2", model="model-2")

        summary = session.get_summary()

        assert summary["session_id"] == session.metadata["session_id"]
        assert summary["message_count"] == 4  # 2 user + 2 assistant
        assert summary["total_tokens_in"] > 0
        assert summary["total_tokens_out"] > 0
        assert summary["total_cost"] > 0
        assert summary["duration_minutes"] >= 0
        assert "model-2" in summary["models_used"]
        assert "mock" in summary["backends_used"]

    def test_export_messages_text(self, mock_router, mock_backend):
        """Test exporting messages as text."""
        session = PersistentChatSession(backend=mock_backend)
        session.history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm doing well!"},
        ]

        text = session.export_messages(format="text")

        assert "User: Hello" in text
        assert "Assistant: Hi there!" in text
        assert "User: How are you?" in text
        assert "Assistant: I'm doing well!" in text

    def test_export_messages_markdown(self, mock_router, mock_backend):
        """Test exporting messages as markdown."""
        session = PersistentChatSession(
            session_id="test-export", system="Test system", backend=mock_backend
        )
        session.history = [{"role": "user", "content": "Test message"}]

        markdown = session.export_messages(format="markdown")

        assert "# Chat Session: test-export" in markdown
        assert "**System:** Test system" in markdown
        assert "### User" in markdown
        assert "Test message" in markdown

    def test_export_messages_json(self, mock_router, mock_backend):
        """Test exporting messages as JSON."""
        session = PersistentChatSession(backend=mock_backend)
        session.history = [{"role": "user", "content": "JSON test"}]

        json_str = session.export_messages(format="json")
        data = json.loads(json_str)

        assert data["session_id"] == session.metadata["session_id"]
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "JSON test"

    def test_export_messages_invalid_format(self, mock_router, mock_backend):
        """Test exporting with invalid format."""
        session = PersistentChatSession(backend=mock_backend)

        with pytest.raises(ValueError) as exc_info:
            session.export_messages(format="pdf")

        assert "Unknown format" in str(exc_info.value)

    def test_clear_history(self, mock_router, mock_backend):
        """Test clearing chat history."""
        session = PersistentChatSession(backend=mock_backend)

        # Add messages
        session.history = [{"role": "user", "content": "Test"}]
        session.metadata["message_count"] = 1
        session.metadata["total_tokens_in"] = 10

        # Clear
        session.clear()

        assert session.history == []
        assert session.metadata["message_count"] == 0
        # Created time should be preserved
        assert "created_at" in session.metadata

    def test_multimodal_metadata(self, mock_router, mock_backend):
        """Test metadata tracking with multimodal inputs."""
        session = PersistentChatSession(backend=mock_backend)

        # Ask with images
        session.ask(["First image", ImageInput("img1.jpg"), ImageInput("img2.jpg")])

        # Check metadata
        assert session.metadata["multimodal_messages"] == 1
        assert session.metadata["total_images"] == 2


class TestDurationCalculation:
    """Test duration calculation functionality."""

    def test_duration_with_iso_timestamps(self, mock_router, mock_backend):
        """Test duration calculation with ISO timestamps."""
        session = PersistentChatSession(backend=mock_backend)

        # Set specific timestamps for created_at and add message with specific timestamp
        start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 10, 30, 45, tzinfo=timezone.utc)

        session.metadata["created_at"] = start.isoformat()
        # Add a message with specific timestamp
        session.history.append(
            {"role": "user", "content": "test message", "timestamp": end.isoformat()}
        )

        summary = session.get_summary()

        # Should be 30.75 minutes (30 minutes and 45 seconds)
        assert abs(summary["duration_minutes"] - 30.75) < 0.01

    def test_duration_with_datetime_objects(self, mock_router, mock_backend):
        """Test duration calculation with one hour duration."""
        session = PersistentChatSession(backend=mock_backend)

        # Set created_at and add message with 1 hour difference
        start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)

        session.metadata["created_at"] = start.isoformat()
        # Add a message with specific timestamp
        session.history.append(
            {"role": "user", "content": "test message", "timestamp": end.isoformat()}
        )

        summary = session.get_summary()

        assert summary["duration_minutes"] == 60.0


class TestTokenEstimation:
    """Test token estimation functionality."""

    def test_estimate_tokens_text(self):
        """Test token estimation for text."""
        # Estimate is len(text) // 4
        assert _estimate_tokens("Hello world") == len("Hello world") // 4  # 11 // 4 = 2
        assert (
            _estimate_tokens("This is a longer sentence with more words")
            == len("This is a longer sentence with more words") // 4
        )

    def test_estimate_tokens_multimodal(self):
        """Test token estimation for multimodal content."""
        content = ["What's in this image?", ImageInput("test.jpg")]

        # Should estimate text tokens + fixed amount for image
        tokens = _estimate_tokens(content)
        assert tokens > 50  # Images add significant tokens

    def test_estimate_tokens_empty(self):
        """Test token estimation for empty input."""
        assert _estimate_tokens("") == 0
        assert _estimate_tokens([]) == 0
