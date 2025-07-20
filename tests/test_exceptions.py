"""Tests for custom exception hierarchy."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from ttt.exceptions import (
    AIError,
    APIKeyError,
    BackendConnectionError,
    BackendNotAvailableError,
    BackendTimeoutError,
    ConfigFileError,
    InvalidParameterError,
    InvalidPromptError,
    ModelNotFoundError,
    MultiModalError,
    PluginLoadError,
    PluginValidationError,
    RateLimitError,
    SessionLoadError,
    SessionSaveError,
)


class TestExceptionHierarchy:
    """Test the exception class hierarchy."""

    def test_all_exceptions_inherit_from_ai_error(self):
        """Test that all exceptions inherit from AIError."""
        exceptions = [
            BackendNotAvailableError("test", "reason"),
            BackendConnectionError("test"),
            ModelNotFoundError("test"),
            APIKeyError("test"),
            ConfigFileError("test.yaml", "reason"),
            InvalidPromptError("reason"),
            SessionLoadError("test.json", "reason"),
        ]

        for exc in exceptions:
            assert isinstance(exc, AIError)
            assert isinstance(exc, Exception)

    def test_exception_messages(self):
        """Test that exceptions have proper messages."""
        exc = BackendNotAvailableError("mybackend", "Not installed")
        assert str(exc) == "Backend 'mybackend' is not available: Not installed"

        exc = ModelNotFoundError("gpt-5", "openai")
        assert str(exc) == "Model 'gpt-5' not found in backend 'openai'"

        exc = APIKeyError("OpenAI", "OPENAI_API_KEY")
        assert "OPENAI_API_KEY" in str(exc)

    def test_exception_details(self):
        """Test that exceptions store details properly."""
        exc = BackendConnectionError("local", Exception("Connection refused"))
        assert exc.details["backend"] == "local"
        assert "Connection refused" in exc.details["original_error"]

        exc = InvalidParameterError("temperature", 2.5, "Must be between 0 and 1")
        assert exc.details["parameter"] == "temperature"
        assert exc.details["value"] == 2.5
        assert exc.details["reason"] == "Must be between 0 and 1"


class TestBackendExceptions:
    """Test backend-related exceptions in actual usage."""

    @patch("ttt.backends.local.httpx.AsyncClient")
    def test_local_backend_connection_error(self, mock_client):
        """Test that connection errors raise BackendConnectionError."""
        import httpx

        from ttt.backends.local import LocalBackend

        # Mock connection error
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        backend = LocalBackend()

        with pytest.raises(BackendConnectionError) as exc_info:
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(backend.ask("Hello"))
            finally:
                loop.close()

        assert "local" in str(exc_info.value)
        assert exc_info.value.details["backend"] == "local"

    @patch("ttt.backends.local.httpx.AsyncClient")
    def test_local_backend_timeout(self, mock_client):
        """Test that timeouts raise BackendTimeoutError."""
        import httpx

        from ttt.backends.local import LocalBackend

        # Mock timeout
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )

        backend = LocalBackend()

        with pytest.raises(BackendTimeoutError) as exc_info:
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(backend.ask("Hello"))
            finally:
                loop.close()

        assert exc_info.value.details["backend"] == "local"
        assert exc_info.value.details["timeout"] == backend.timeout

    def test_local_backend_multimodal_error(self):
        """Test that multi-modal input raises MultiModalError."""
        from ttt.backends.local import LocalBackend
        from ttt.models import ImageInput

        backend = LocalBackend()

        with pytest.raises(MultiModalError) as exc_info:
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    backend.ask(["What's this?", ImageInput("test.jpg")])
                )
            finally:
                loop.close()

        assert "Ollama" in str(exc_info.value)
        assert "vision" in str(exc_info.value)

    @patch("ttt.backends.local.httpx.AsyncClient")
    def test_model_not_found(self, mock_client):
        """Test that 404 errors for models raise ModelNotFoundError."""
        import httpx

        from ttt.backends.local import LocalBackend

        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "model not found"

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not found", request=Mock(), response=mock_response
            )
        )

        backend = LocalBackend()

        with pytest.raises(ModelNotFoundError) as exc_info:
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(backend.ask("Hello", model="nonexistent"))
            finally:
                loop.close()

        assert exc_info.value.details["model"] == "nonexistent"
        assert exc_info.value.details["backend"] == "local"


class TestCloudBackendExceptions:
    """Test cloud backend exception handling."""

    def test_litellm_not_installed(self):
        """Test that missing LiteLLM raises BackendNotAvailableError."""
        with patch.dict("sys.modules", {"litellm": None}):
            from ttt.backends.cloud import CloudBackend

            with pytest.raises(BackendNotAvailableError) as exc_info:
                CloudBackend()

            assert "LiteLLM" in str(exc_info.value)
            assert exc_info.value.details["backend"] == "cloud"

    def test_api_key_error(self):
        """Test that authentication errors raise APIKeyError."""
        from ttt.backends.cloud import CloudBackend

        backend = CloudBackend()

        # Mock the instance's litellm.acompletion method
        backend.litellm.acompletion = AsyncMock(
            side_effect=Exception("api_key is required")
        )

        with pytest.raises(APIKeyError) as exc_info:
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(backend.ask("Hello", model="gpt-3.5-turbo"))
            finally:
                loop.close()

        assert exc_info.value.details["provider"] == "openai"
        assert exc_info.value.details["env_var"] == "OPENAI_API_KEY"

    def test_rate_limit_error(self):
        """Test that rate limit errors are handled properly."""
        from ttt.backends.cloud import CloudBackend

        backend = CloudBackend()

        # Mock the instance's litellm.acompletion method
        backend.litellm.acompletion = AsyncMock(
            side_effect=Exception("Rate limit exceeded")
        )

        with pytest.raises(RateLimitError) as exc_info:
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    backend.ask("Hello", model="claude-3-sonnet-20240229")
                )
            finally:
                loop.close()

        assert exc_info.value.details["provider"] == "anthropic"


class TestConfigExceptions:
    """Test configuration-related exceptions."""

    def test_invalid_yaml_config(self, tmp_path):
        """Test that invalid YAML raises ConfigFileError."""
        from ttt.config import load_config

        # Create invalid YAML
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: {]}")

        with pytest.raises(ConfigFileError) as exc_info:
            load_config(config_file)

        assert str(config_file) in exc_info.value.details["file_path"]
        assert "YAML parsing error" in exc_info.value.details["reason"]

    def test_unsupported_config_format(self, tmp_path):
        """Test that unsupported formats raise ConfigFileError."""
        from ttt.config import load_config

        # Create config with unsupported extension
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")

        with pytest.raises(ConfigFileError) as exc_info:
            load_config(config_file)

        assert "Unsupported config file format" in str(exc_info.value)


class TestSessionExceptions:
    """Test session-related exceptions."""

    def test_session_load_not_found(self):
        """Test loading non-existent session raises SessionLoadError."""
        from ttt.chat import PersistentChatSession

        with pytest.raises(SessionLoadError) as exc_info:
            PersistentChatSession.load("nonexistent.json")

        assert "File not found" in exc_info.value.details["reason"]
        assert "nonexistent.json" in exc_info.value.details["file_path"]

    def test_session_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises SessionLoadError."""
        from ttt.chat import PersistentChatSession

        # Create invalid JSON
        session_file = tmp_path / "invalid.json"
        session_file.write_text("{invalid json}")

        with pytest.raises(SessionLoadError) as exc_info:
            PersistentChatSession.load(session_file)

        assert "Invalid JSON" in exc_info.value.details["reason"]

    def test_session_save_invalid_format(self):
        """Test saving with invalid format raises InvalidParameterError."""
        from ttt.chat import PersistentChatSession

        session = PersistentChatSession()

        with pytest.raises(InvalidParameterError) as exc_info:
            session.save("test.txt", format="xml")

        assert exc_info.value.details["parameter"] == "format"
        assert exc_info.value.details["value"] == "xml"
        assert "json" in exc_info.value.details["reason"]

    def test_session_save_permission_error(self, tmp_path):
        """Test saving to protected location raises SessionSaveError."""
        from ttt.chat import PersistentChatSession

        session = PersistentChatSession()

        # Try to save to a read-only directory
        protected_dir = tmp_path / "protected"
        protected_dir.mkdir()
        protected_file = protected_dir / "session.json"

        # Make directory read-only
        protected_dir.chmod(0o444)

        try:
            with pytest.raises(SessionSaveError) as exc_info:
                session.save(protected_file)

            assert str(protected_file) in exc_info.value.details["file_path"]
        finally:
            # Restore permissions for cleanup
            protected_dir.chmod(0o755)


class TestPluginExceptions:
    """Test plugin-related exceptions."""

    def test_plugin_load_error(self, tmp_path):
        """Test that plugin load errors are handled properly."""
        from ttt.plugins import PluginRegistry

        # Create a plugin with syntax error
        plugin_file = tmp_path / "bad_plugin.py"
        plugin_file.write_text(
            "def register_plugin(registry)\n    pass"
        )  # Missing colon

        registry = PluginRegistry()

        with pytest.raises(PluginLoadError) as exc_info:
            registry._load_plugin_from_file(plugin_file)

        assert str(plugin_file) in exc_info.value.details["plugin_path"]

    def test_plugin_validation_error(self, tmp_path):
        """Test that plugins without register_plugin raise PluginValidationError."""
        from ttt.plugins import PluginRegistry

        # Create a plugin without register_plugin
        plugin_file = tmp_path / "invalid_plugin.py"
        plugin_file.write_text("# No register_plugin function")

        registry = PluginRegistry()

        with pytest.raises(PluginValidationError) as exc_info:
            registry._load_plugin_from_file(plugin_file)

        assert "register_plugin" in exc_info.value.details["reason"]


class TestRoutingExceptions:
    """Test routing-related exceptions."""

    def test_unknown_backend(self):
        """Test that unknown backends raise BackendNotAvailableError."""
        from ttt.routing import Router

        router = Router()

        with pytest.raises(BackendNotAvailableError) as exc_info:
            router.get_backend("nonexistent")

        assert "nonexistent" in str(exc_info.value)
        assert exc_info.value.details["backend"] == "nonexistent"
