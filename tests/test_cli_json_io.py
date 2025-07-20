"""Tests for CLI JSON input/output and piping functionality."""

import json
from unittest.mock import Mock, patch

from click.testing import CliRunner

from ttt.cli import main


class TestJSONInputOutput:
    """Test JSON input/output functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

        # Create a standard mock response
        self.mock_response = Mock()
        self.mock_response.__str__ = Mock(return_value="Test response")
        self.mock_response.model = "gpt-3.5-turbo"
        self.mock_response.backend = "cloud"
        self.mock_response.time = 1.0
        self.mock_response.tokens_in = 10
        self.mock_response.tokens_out = 5

    def test_json_output_format(self):
        """Test --json flag produces correct JSON output."""
        with patch("ttt.ask") as mock_ask:
            mock_ask.return_value = self.mock_response

            result = self.runner.invoke(main, ["test prompt", "--json"])

            assert result.exit_code == 0

            # Parse and verify JSON output
            output_data = json.loads(result.output.strip())
            assert output_data["content"] == "Test response"
            assert output_data["model"] == "gpt-3.5-turbo"
            assert output_data["backend"] == "cloud"
            assert output_data["time"] == 1.0
            assert output_data["streaming"] is False
            assert output_data["tokens_in"] == 10
            assert output_data["tokens_out"] == 5

    def test_json_input_with_prompt_field(self):
        """Test JSON input parsing with 'prompt' field."""
        json_input = '{"prompt": "what is 2+2?", "model": "custom-model"}'

        with patch("ttt.ask") as mock_ask:
            mock_ask.return_value = self.mock_response

            result = self.runner.invoke(main, ["-"], input=json_input)

            assert result.exit_code == 0
            # Verify ttt.ask was called with extracted values
            mock_ask.assert_called_once()
            call_args, call_kwargs = mock_ask.call_args
            assert call_args[0] == "what is 2+2?"
            assert call_kwargs.get("model") == "custom-model"

    def test_json_input_with_query_field(self):
        """Test JSON input parsing with 'query' field."""
        json_input = '{"query": "capital of France?", "temperature": 0.7}'

        with patch("ttt.ask") as mock_ask:
            mock_ask.return_value = self.mock_response

            result = self.runner.invoke(main, ["-"], input=json_input)

            assert result.exit_code == 0
            call_args, call_kwargs = mock_ask.call_args
            assert call_args[0] == "capital of France?"
            assert call_kwargs.get("temperature") == 0.7

    def test_json_input_with_message_field(self):
        """Test JSON input parsing with 'message' field."""
        json_input = '{"message": "translate hello", "max_tokens": 100}'

        with patch("ttt.ask") as mock_ask:
            mock_ask.return_value = self.mock_response

            result = self.runner.invoke(main, ["-"], input=json_input)

            assert result.exit_code == 0
            call_args, call_kwargs = mock_ask.call_args
            assert call_args[0] == "translate hello"
            assert call_kwargs.get("max_tokens") == 100

    def test_json_input_with_content_field(self):
        """Test JSON input parsing with 'content' field."""
        json_input = '{"content": "tell a joke", "system": "be funny"}'

        with patch("ttt.ask") as mock_ask:
            mock_ask.return_value = self.mock_response

            result = self.runner.invoke(main, ["-"], input=json_input)

            assert result.exit_code == 0
            call_args, call_kwargs = mock_ask.call_args
            assert call_args[0] == "tell a joke"
            assert call_kwargs.get("system") == "be funny"

    def test_json_input_with_text_field(self):
        """Test JSON input parsing with 'text' field."""
        json_input = '{"text": "explain AI"}'

        with patch("ttt.ask") as mock_ask:
            mock_ask.return_value = self.mock_response

            result = self.runner.invoke(main, ["-"], input=json_input)

            assert result.exit_code == 0
            call_args, call_kwargs = mock_ask.call_args
            assert call_args[0] == "explain AI"

    def test_invalid_json_fallback_to_text(self):
        """Test that invalid JSON falls back to plain text."""
        text_input = "plain text input {not json"

        with patch("ttt.ask") as mock_ask:
            mock_ask.return_value = self.mock_response

            result = self.runner.invoke(main, ["-"], input=text_input)

            assert result.exit_code == 0
            call_args, call_kwargs = mock_ask.call_args
            assert call_args[0] == text_input

    def test_json_input_no_recognized_field(self):
        """Test JSON without recognized prompt field uses entire JSON."""
        json_input = '{"unknown": "value", "other": "data"}'

        with patch("ttt.ask") as mock_ask:
            mock_ask.return_value = self.mock_response

            result = self.runner.invoke(main, ["-"], input=json_input)

            assert result.exit_code == 0
            call_args, call_kwargs = mock_ask.call_args
            assert call_args[0] == json_input

    def test_json_error_output(self):
        """Test JSON error output format."""
        with patch("ttt.ask") as mock_ask:
            mock_ask.side_effect = Exception("Test error message")

            result = self.runner.invoke(main, ["test prompt", "--json"])

            assert result.exit_code == 1
            output_data = json.loads(result.output.strip())
            assert "error" in output_data
            assert "Test error message" in output_data["error"]

    def test_json_streaming_output(self):
        """Test JSON streaming output."""
        with patch("ttt.stream") as mock_stream:
            mock_stream.return_value = ["Hello", " ", "world", "!"]

            result = self.runner.invoke(main, ["test prompt", "--stream", "--json"])

            assert result.exit_code == 0
            output_data = json.loads(result.output.strip())
            assert output_data["content"] == "Hello world!"
            assert output_data["streaming"] is True

    def test_json_output_without_token_info(self):
        """Test JSON output when response has no token info."""
        mock_response_no_tokens = Mock()
        mock_response_no_tokens.__str__ = Mock(return_value="Response")
        mock_response_no_tokens.model = "gpt-3.5-turbo"
        mock_response_no_tokens.backend = "cloud"
        mock_response_no_tokens.time = 1.0

        # Explicitly set tokens_in to None so hasattr returns True but value is None
        mock_response_no_tokens.tokens_in = None
        mock_response_no_tokens.tokens_out = None

        with patch("ttt.ask") as mock_ask:
            mock_ask.return_value = mock_response_no_tokens

            result = self.runner.invoke(main, ["test", "--json"])

            assert result.exit_code == 0
            output_data = json.loads(result.output.strip())
            assert "content" in output_data
            assert "model" in output_data
            # Should not include token info when tokens_in is None/falsy
            assert "tokens_in" not in output_data
            assert "tokens_out" not in output_data


class TestDefaultAskBehavior:
    """Test default ask behavior without explicit 'ask' command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_command_line_argument_defaults_to_ask(self):
        """Test that providing an argument defaults to direct prompt."""
        with patch("ttt.ask") as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_response.model = "gpt-3.5-turbo"
            mock_response.backend = "cloud"
            mock_response.time = 0.5
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ["what is Python?"])

            assert result.exit_code == 0
            assert "Response" in result.output
            call_args, call_kwargs = mock_ask.call_args
            assert call_args[0] == "what is Python?"

    def test_stdin_input_defaults_to_ask(self):
        """Test that stdin input defaults to direct prompt."""
        with patch("ttt.ask") as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Stdin response")
            mock_response.model = "gpt-3.5-turbo"
            mock_response.backend = "cloud"
            mock_response.time = 0.5
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ["-"], input="stdin input text")

            assert result.exit_code == 0
            assert "Stdin response" in result.output
            call_args, call_kwargs = mock_ask.call_args
            assert call_args[0] == "stdin input text"

    def test_no_arguments_shows_help(self):
        """Test that no arguments shows help or error."""
        result = self.runner.invoke(main, [])

        # Should either show help (exit 0) or no input error (exit 1)
        assert result.exit_code in (0, 1)
        assert (
            "TTT" in result.output
            or "No input provided" in result.output
            or "help" in result.output.lower()
        )


class TestCompleteJSONWorkflow:
    """Test end-to-end JSON workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_json_in_json_out_complete_workflow(self):
        """Test complete JSON input to JSON output workflow."""
        json_input = '{"prompt": "what is AI?", "model": "gpt-4", "temperature": 0.3}'

        with patch("ttt.ask") as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="AI is artificial intelligence")
            mock_response.model = "gpt-4"
            mock_response.backend = "cloud"
            mock_response.time = 2.5
            mock_response.tokens_in = 20
            mock_response.tokens_out = 15
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ["-", "--json"], input=json_input)

            assert result.exit_code == 0

            # Verify input parsing
            call_args, call_kwargs = mock_ask.call_args
            assert call_args[0] == "what is AI?"
            assert call_kwargs.get("model") == "gpt-4"
            assert call_kwargs.get("temperature") == 0.3

            # Verify JSON output
            output_data = json.loads(result.output.strip())
            assert output_data["content"] == "AI is artificial intelligence"
            assert output_data["model"] == "gpt-4"
            assert output_data["backend"] == "cloud"
            assert output_data["time"] == 2.5
            assert output_data["tokens_in"] == 20
            assert output_data["tokens_out"] == 15
            assert output_data["streaming"] is False

    def test_text_in_json_out_workflow(self):
        """Test plain text input with JSON output."""

        # Create a simple class instead of Mock to avoid JSON serialization issues
        class SimpleResponse:
            def __init__(self):
                self.model = "gpt-3.5-turbo"
                self.backend = "cloud"
                self.time = 1.2

            def __str__(self):
                return "Text response"

        with patch("ttt.ask") as mock_ask:
            mock_ask.return_value = SimpleResponse()

            result = self.runner.invoke(
                main, ["-", "--json"], input="simple text query"
            )

            assert result.exit_code == 0

            # Verify input was treated as plain text
            call_args, call_kwargs = mock_ask.call_args
            assert call_args[0] == "simple text query"

            # Verify JSON output
            output_data = json.loads(result.output.strip())
            assert output_data["content"] == "Text response"
            assert output_data["streaming"] is False
