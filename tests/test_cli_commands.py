"""Tests for CLI commands."""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import subprocess
import sys
import os

# Import functions from the CLI directly since it's not a typer app
from ai.cli import show_backend_status, show_models_list, parse_args, main, show_help
from ai.backends.local import LocalBackend
from ai.backends.cloud import CloudBackend
from ai.api import ask, stream


class TestModelsCommands:
    """Test the models-list command."""

    @patch("ai.backends.LocalBackend")
    @patch("httpx.get")
    def test_models_list_all(self, mock_httpx_get, mock_local_backend):
        """Test listing all models."""
        # Mock local backend
        mock_backend_instance = Mock()
        mock_backend_instance.is_available = True
        mock_backend_instance.base_url = "http://localhost:11434"
        mock_local_backend.return_value = mock_backend_instance

        # Mock Ollama API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "llama2"}, {"name": "codellama"}]
        }
        mock_httpx_get.return_value = mock_response

        # Capture output
        with patch("ai.cli.console") as mock_console:
            show_models_list()

            # Check that models were printed
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("llama2" in str(call) for call in print_calls)
            assert any("codellama" in str(call) for call in print_calls)

    @patch("ai.backends.LocalBackend")
    def test_models_list_no_local_backend(self, mock_local_backend):
        """Test listing models when local backend is not available."""
        # Mock local backend not available
        mock_backend_instance = Mock()
        mock_backend_instance.is_available = False
        mock_local_backend.return_value = mock_backend_instance

        # Capture output
        with patch("ai.cli.console") as mock_console:
            show_models_list()

            # Check that appropriate message was shown
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            assert any(
                "Local backend not available" in str(call) for call in print_calls
            )

    @patch("ai.backends.LocalBackend")
    @patch("httpx.get")
    def test_models_list_ollama_error(self, mock_httpx_get, mock_local_backend):
        """Test listing models when Ollama returns an error."""
        # Mock local backend available
        mock_backend_instance = Mock()
        mock_backend_instance.is_available = True
        mock_backend_instance.base_url = "http://localhost:11434"
        mock_local_backend.return_value = mock_backend_instance

        # Mock Ollama API error
        mock_httpx_get.side_effect = Exception("Connection error")

        # Capture output
        with patch("ai.cli.console") as mock_console:
            show_models_list()

            # Check error handling
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            assert any(
                "Ollama not running or not accessible" in str(call)
                for call in print_calls
            )


class TestBackendCommands:
    """Test the backend-status command."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("ai.backends.LocalBackend")
    def test_backend_status_basic(self, mock_local_backend):
        """Test basic backend status check."""
        # Mock local backend
        mock_backend_instance = Mock()
        mock_backend_instance.is_available = True
        mock_backend_instance.base_url = "http://localhost:11434"
        mock_backend_instance.default_model = "llama2"
        mock_local_backend.return_value = mock_backend_instance

        # Capture output
        with patch("ai.cli.console") as mock_console:
            show_backend_status()

            # Check output
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("Backend Status" in str(call) for call in print_calls)
            assert any("Local Backend" in str(call) for call in print_calls)
            assert any("Available" in str(call) for call in print_calls)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"}, clear=True)
    @patch("ai.backends.CloudBackend")
    def test_backend_status_with_api_key(self, mock_cloud_backend):
        """Test backend status with API key present."""
        # Mock cloud backend
        mock_backend_instance = Mock()
        mock_backend_instance.is_available = True
        mock_backend_instance.default_model = "gpt-3.5-turbo"
        mock_cloud_backend.return_value = mock_backend_instance

        # Capture output
        with patch("ai.cli.console") as mock_console:
            show_backend_status()

            # Check output
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("Cloud Backend" in str(call) for call in print_calls)
            assert any("Available" in str(call) for call in print_calls)
            assert any("OPENAI" in str(call) for call in print_calls)

    @patch("ai.backends.LocalBackend")
    def test_backend_status_connection_error(self, mock_local_backend):
        """Test backend status with connection errors."""
        # Mock connection error
        mock_local_backend.side_effect = Exception("Connection refused")

        # Capture output
        with patch("ai.cli.console") as mock_console:
            show_backend_status()

            # Check error handling
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            assert any("Error" in str(call) for call in print_calls)


class TestMainCommand:
    """Test main command functionality."""

    def test_parse_args_help(self):
        """Test parsing --help argument."""
        with patch("sys.argv", ["ai", "--help"]):
            args = parse_args()
            assert args["command"] == "help"

    def test_parse_args_backend_status(self):
        """Test parsing backend-status command."""
        with patch("sys.argv", ["ai", "backend-status"]):
            args = parse_args()
            assert args["command"] == "backend-status"

    def test_parse_args_models_list(self):
        """Test parsing models-list command."""
        with patch("sys.argv", ["ai", "models-list"]):
            args = parse_args()
            assert args["command"] == "models-list"

    def test_parse_args_query_basic(self):
        """Test parsing basic query."""
        with patch("sys.argv", ["ai", "What is Python?"]):
            args = parse_args()
            assert args["command"] == "query"
            assert args["prompt"] == "What is Python?"
            assert args["model"] is None
            assert args["stream"] is False

    def test_parse_args_query_with_model(self):
        """Test parsing query with model."""
        with patch("sys.argv", ["ai", "Question", "--model", "gpt-4"]):
            args = parse_args()
            assert args["command"] == "query"
            assert args["prompt"] == "Question"
            assert args["model"] == "gpt-4"

    def test_parse_args_query_with_stream(self):
        """Test parsing query with stream flag."""
        with patch("sys.argv", ["ai", "Question", "--stream"]):
            args = parse_args()
            assert args["command"] == "query"
            assert args["prompt"] == "Question"
            assert args["stream"] is True

    def test_parse_args_query_with_backend(self):
        """Test parsing query with backend."""
        with patch("sys.argv", ["ai", "Question", "--backend", "local"]):
            args = parse_args()
            assert args["command"] == "query"
            assert args["prompt"] == "Question"
            assert args["backend"] == "local"

    def test_main_help(self):
        """Test main function with help command."""
        with patch("sys.argv", ["ai", "--help"]):
            with patch("ai.cli.show_help") as mock_help:
                main()
                mock_help.assert_called_once()

    @patch("ai.api.ask")
    def test_main_query(self, mock_ask):
        """Test main function with query."""
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Test response")
        mock_response.model = "test-model"
        mock_response.backend = "test-backend"
        mock_response.time = 0.5
        mock_ask.return_value = mock_response

        with patch("sys.argv", ["ai", "Test question"]):
            with patch("ai.cli.console") as mock_console:
                main()

                # Check that response was printed
                print_calls = [str(call) for call in mock_console.print.call_args_list]
                assert any("Test response" in str(call) for call in print_calls)

    @patch("ai.api.stream")
    def test_main_stream(self, mock_stream):
        """Test main function with streaming."""
        mock_stream.return_value = iter(["Hello", " ", "world"])

        with patch("sys.argv", ["ai", "Test question", "--stream"]):
            with patch("ai.cli.console") as mock_console:
                main()

                # Check that stream was processed
                print_calls = [
                    call[0][0] if call[0] else ""
                    for call in mock_console.print.call_args_list
                ]
                # The streaming output might be combined or separate
                output = "".join(str(call) for call in print_calls)
                assert "Hello" in output and "world" in output
