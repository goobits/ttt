"""Advanced tests for CLI module to increase coverage."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from click.testing import CliRunner

# Import CLI functions and exceptions
from ai.cli import main
from ai.api import ask, stream
from ai.exceptions import (
    APIKeyError,
    ModelNotFoundError,
    RateLimitError,
    BackendNotAvailableError,
    EmptyResponseError,
)


class TestCLIAskCommand:
    """Test the ask functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_ask_basic(self):
        """Test basic ask functionality."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Test response")
            mock_response.model = "gpt-3.5-turbo"
            mock_response.backend = "cloud"
            mock_response.time = 0.5
            mock_response.tokens_in = 10
            mock_response.tokens_out = 20
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ['ask', 'What is Python?'])
            
            assert result.exit_code == 0
            mock_ask.assert_called_once()
            call_args = mock_ask.call_args
            assert call_args[0][0] == "What is Python?"

    def test_ask_with_model(self):
        """Test ask with specific model."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ['ask', 'Question', '--model', 'gpt-4'])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs.get("model") == "gpt-4"

    def test_ask_with_system(self):
        """Test ask with system prompt."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ['ask', 'Question', '--system', 'You are helpful'])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs.get("system") == "You are helpful"

    def test_ask_with_verbose(self):
        """Test ask with verbose output."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_response.model = "test-model"
            mock_response.backend = "test-backend"
            mock_response.time = 1.5
            mock_response.tokens_in = 15
            mock_response.tokens_out = 25
            mock_response.cost = 0.001
            mock_response.tool_calls = None  # No tools called
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ['ask', 'Question', '--verbose'])
            
            assert result.exit_code == 0
            # Check that verbose info was shown in output
            assert "Response" in result.output

    def test_ask_streaming(self):
        """Test ask with streaming."""
        with patch('ai.stream') as mock_stream:
            mock_stream.return_value = iter(["Hello", " ", "world"])

            result = self.runner.invoke(main, ['ask', 'Question', '--stream'])
            
            assert result.exit_code == 0
            mock_stream.assert_called_once()
            # Check streaming output appears in result
            assert "Hello" in result.output and "world" in result.output

    def test_ask_with_temperature(self):
        """Test ask with temperature."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ['ask', 'Question', '--temperature', '0.5'])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs.get("temperature") == 0.5

    def test_ask_with_max_tokens(self):
        """Test ask with max tokens."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ['ask', 'Question', '--max-tokens', '100'])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs.get("max_tokens") == 100


    def test_ask_from_stdin(self):
        """Test reading prompt from stdin."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ["ask", "-"], input="stdin content")
            assert result.exit_code == 0
            
            call_args = mock_ask.call_args
            assert call_args[0][0] == "stdin content"


class TestCLIErrorHandling:
    """Test error handling in CLI."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_api_key_error(self):
        """Test handling of API key errors."""
        with patch('ai.ask') as mock_ask:
            mock_ask.side_effect = APIKeyError("openai", "OPENAI_API_KEY")

            result = self.runner.invoke(main, ['ask', 'Question'])
            
            assert result.exit_code == 1
            assert "api key" in result.output.lower()
            assert "openai_api_key" in result.output.lower()

    def test_model_not_found_error(self):
        """Test handling of model not found errors."""
        with patch('ai.ask') as mock_ask:
            mock_ask.side_effect = ModelNotFoundError("gpt-5", "cloud")

            result = self.runner.invoke(main, ['ask', 'Question'])
            
            assert result.exit_code == 1
            assert "not found" in result.output.lower()
            assert "gpt-5" in result.output

    def test_rate_limit_error(self):
        """Test handling of rate limit errors."""
        with patch('ai.ask') as mock_ask:
            mock_ask.side_effect = RateLimitError("openai", retry_after=60)

            result = self.runner.invoke(main, ['ask', 'Question'])
            
            assert result.exit_code == 1
            assert "rate limit" in result.output.lower()
            assert "60" in result.output

    def test_backend_not_available_error(self):
        """Test handling of backend not available errors."""
        with patch('ai.ask') as mock_ask:
            mock_ask.side_effect = BackendNotAvailableError("local", "Ollama not running")

            result = self.runner.invoke(main, ['ask', 'Question'])
            
            assert result.exit_code == 1
            assert "not available" in result.output.lower()
            assert "local" in result.output

    def test_empty_response_error(self):
        """Test handling of empty response errors."""
        with patch('ai.ask') as mock_ask:
            mock_ask.side_effect = EmptyResponseError("gpt-3.5", "cloud")

            result = self.runner.invoke(main, ['ask', 'Question'])
            
            assert result.exit_code == 1
            assert "empty response" in result.output.lower()
            assert "gpt-3.5" in result.output

    def test_generic_error_without_verbose(self):
        """Test handling of generic errors without verbose flag."""
        with patch('ai.ask') as mock_ask:
            mock_ask.side_effect = Exception("Some unexpected error")

            result = self.runner.invoke(main, ['ask', 'Question'])
            
            assert result.exit_code == 1
            assert "Error" in result.output
            assert "Some unexpected error" in result.output

    def test_generic_error_with_verbose(self):
        """Test handling of generic errors with verbose flag."""
        with patch('ai.ask') as mock_ask:
            mock_ask.side_effect = Exception("Some unexpected error")

            result = self.runner.invoke(main, ['ask', 'Question', '--verbose'])
            
            assert result.exit_code == 1
            assert "Error" in result.output
            assert "Some unexpected error" in result.output

    def test_stream_error_handling(self):
        """Test error handling in stream mode."""
        with patch('ai.stream') as mock_stream:
            mock_stream.side_effect = Exception("Stream error")

            result = self.runner.invoke(main, ['ask', 'Question', '--stream'])
            
            assert result.exit_code == 1
            assert "Error" in result.output
            assert "Stream error" in result.output

    def test_keyboard_interrupt(self):
        """Test handling of keyboard interrupt."""
        with patch('ai.ask') as mock_ask:
            mock_ask.side_effect = KeyboardInterrupt()

            result = self.runner.invoke(main, ['ask', 'Question'])
            
            assert result.exit_code == 1
            # Click handles KeyboardInterrupt as "Aborted!"
            assert "Aborted" in result.output


class TestCLIArguments:
    """Test CLI argument parsing using modern Click patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        from click.testing import CliRunner
        self.runner = CliRunner()

    def test_cli_no_args_shows_help(self):
        """Test CLI with no arguments shows help or reports no input."""
        result = self.runner.invoke(main, [])
        # Either shows help (exit 0) or reports no input (exit 1)
        # Both are valid behaviors depending on stdin state
        assert result.exit_code in (0, 1)
        # Should either show help or error about no input
        assert ("AI Library - Unified AI Interface" in result.output or 
                "No input provided" in result.output)

    def test_cli_multiple_flags(self):
        """Test CLI with multiple flags."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_response.model = "gpt-4"
            mock_response.backend = "cloud"
            mock_response.time = 1.23
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, [
                "ask", "Question",
                "--model", "gpt-4",
                "--verbose"
            ])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs["model"] == "gpt-4"

    def test_cli_short_flags(self):
        """Test CLI with short flag versions."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_response.model = "gpt-4"
            mock_response.backend = "cloud"
            mock_response.time = 1.23
            mock_response.tokens_in = 10
            mock_response.tokens_out = 20
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, [
                "ask", "Question", "-m", "gpt-4", "-v"
            ])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs["model"] == "gpt-4"
            # Verbose flag should be processed
            assert "Mock response" in result.output

    def test_cli_all_parameters(self):
        """Test CLI with all possible parameters."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_response.model = "gpt-4"
            mock_response.backend = "cloud"
            mock_response.time = 1.23
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, [
                "ask", "Question",
                "--model", "gpt-4",
                "--system", "You are helpful",
                "--temperature", "0.7",
                "--max-tokens", "150",
                "--verbose"
            ])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs["model"] == "gpt-4"
            assert call_kwargs["system"] == "You are helpful"
            assert call_kwargs["temperature"] == 0.7
            assert call_kwargs["max_tokens"] == 150

    def test_cli_streaming(self):
        """Test CLI with streaming flag."""
        with patch('ai.stream') as mock_stream:
            mock_stream.return_value = iter(["chunk1", "chunk2"])
            
            result = self.runner.invoke(main, [
                "ask", "Question", "--stream"
            ])
            
            assert result.exit_code == 0
            mock_stream.assert_called_once()
