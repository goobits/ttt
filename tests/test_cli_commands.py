"""Tests for CLI commands."""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import subprocess
import sys
import os

# Import functions from the CLI
from ai.cli import show_backend_status, show_models_list, main
from ai.backends.local import LocalBackend
from ai.backends.cloud import CloudBackend
from ai.api import ask, stream


class TestModelsCommands:
    """Test the models-list command."""

    @patch("ai.backends.local.LocalBackend")
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
            
            # Debug: print what's actually being called
            # for call in print_calls:
            #     print(f"DEBUG: {call}")
            
            # The models are printed as "• llama2", not just "llama2"
            # Check for the bullet format
            assert any("llama2" in str(call) for call in print_calls)
            assert any("codellama" in str(call) for call in print_calls)
            # Also check that cloud models are shown
            assert any("gpt-4o" in str(call) or "gpt-3.5-turbo" in str(call) for call in print_calls)

    @patch("ai.backends.local.LocalBackend")
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

    @patch("ai.backends.local.LocalBackend")
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
    @patch("ai.backends.local.LocalBackend")
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
    @patch("ai.backends.cloud.CloudBackend")
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

    @patch("ai.backends.local.LocalBackend")
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
    """Test main command functionality using modern Click patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        from click.testing import CliRunner
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test --help argument."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "AI Library - Unified AI Interface" in result.output

    def test_backend_status_command(self):
        """Test backend-status command."""
        with patch("ai.cli.show_backend_status") as mock_status:
            result = self.runner.invoke(main, ["backend-status"])
            assert result.exit_code == 0
            mock_status.assert_called_once()

    def test_models_list_command(self):
        """Test models-list command."""
        with patch("ai.cli.show_models_list") as mock_models:
            result = self.runner.invoke(main, ["models-list"])
            assert result.exit_code == 0
            mock_models.assert_called_once()

    def test_ask_basic_query(self):
        """Test basic ask query."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ["ask", "What is Python?"])
            assert result.exit_code == 0
            
            call_args = mock_ask.call_args
            assert call_args[0][0] == "What is Python?"

    def test_ask_with_model(self):
        """Test ask query with model."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ["ask", "Question", "--model", "gpt-4"])
            assert result.exit_code == 0
            
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs["model"] == "gpt-4"

    def test_ask_with_stream(self):
        """Test ask query with stream flag."""
        with patch('ai.stream') as mock_stream:
            mock_stream.return_value = iter(["chunk1", "chunk2"])
            
            result = self.runner.invoke(main, ["ask", "Question", "--stream"])
            assert result.exit_code == 0
            mock_stream.assert_called_once()

    def test_ask_with_backend(self):
        """Test ask query with backend."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ["ask", "Question", "--offline"])
            assert result.exit_code == 0
            
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs["backend"] == "local"

    def test_main_query(self):
        """Test main function with query."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Test response")
            mock_response.model = "test-model"
            mock_response.backend = "test-backend"
            mock_response.time = 0.5
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ['ask', 'Test question'])
            
            assert result.exit_code == 0
            assert "Test response" in result.output

    def test_main_stream(self):
        """Test main function with streaming."""
        with patch('ai.stream') as mock_stream:
            mock_stream.return_value = iter(["Hello", " ", "world"])

            result = self.runner.invoke(main, ['ask', 'Test question', '--stream'])
            
            assert result.exit_code == 0
            assert "Hello" in result.output and "world" in result.output
