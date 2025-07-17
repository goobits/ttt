"""Modern CLI tests using Click's testing facilities."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, Mock
from ai.cli import main


class TestClickCLI:
    """Test the refactored Click-based CLI."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_direct_prompt_basic(self):
        """Test basic direct prompt functionality."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ["What is Python?"])
            
            assert result.exit_code == 0
            mock_ask.assert_called_once()
            call_args = mock_ask.call_args
            assert call_args[0][0] == "What is Python?"

    def test_direct_prompt_with_options(self):
        """Test direct prompt with various options."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_response.model = "gpt-4"
            mock_response.backend = "cloud"
            mock_response.time = 1.23
            mock_response.tokens_in = 10
            mock_response.tokens_out = 20
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, [
                "Debug this code",
                "--model", "gpt-4",
                "--temperature", "0.7",
                "--verbose",
                "--code"
            ])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs["model"] == "gpt-4"
            assert call_kwargs["temperature"] == 0.7


    def test_direct_prompt_stdin(self):
        """Test direct prompt with stdin input."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ["-"], input="Input from stdin")
            
            assert result.exit_code == 0
            call_args = mock_ask.call_args
            assert call_args[0][0] == "Input from stdin"

    def test_chat_command(self):
        """Test chat command."""
        with patch('ai.chat') as mock_chat_context:
            mock_session = Mock()
            mock_chat_context.return_value.__enter__ = lambda x: mock_session
            mock_chat_context.return_value.__exit__ = lambda x, *args: None
            
            # Simulate immediate exit from chat
            with patch('click.prompt', side_effect=EOFError):
                result = self.runner.invoke(main, [
                    "--chat",
                    "--model", "claude-3-sonnet",
                    "--system", "You are helpful",
                    "--verbose"
                ])
            
            assert result.exit_code == 0
            mock_chat_context.assert_called_once()

    def test_backend_status_command(self):
        """Test status command."""
        with patch('ai.cli.show_backend_status') as mock_status:
            result = self.runner.invoke(main, ["--status"])
            
            assert result.exit_code == 0
            mock_status.assert_called_once()

    def test_models_list_command(self):
        """Test models command."""
        with patch('ai.cli.show_models_list') as mock_models:
            result = self.runner.invoke(main, ["--models"])
            
            assert result.exit_code == 0
            mock_models.assert_called_once()

    def test_tools_list_command(self):
        """Test tools command."""
        with patch('ai.cli.show_tools_list') as mock_tools:
            result = self.runner.invoke(main, ["--tools-list"])
            
            assert result.exit_code == 0
            mock_tools.assert_called_once()

    def test_help_display(self):
        """Test that help is displayed correctly."""
        result = self.runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        assert "TTT - Text-to-Text Processing Library" in result.stdout
        assert "--chat" in result.stdout
        assert "--status" in result.stdout

    def test_command_help(self):
        """Test individual command help."""
        result = self.runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        assert "TTT - Text-to-Text Processing Library" in result.stdout
        assert "--model" in result.stdout
        assert "--model" in result.stdout

    def test_invalid_arguments(self):
        """Test handling of invalid arguments."""
        # No arguments shows help (exit 0) or no input error (exit 1)
        result = self.runner.invoke(main, [])
        assert result.exit_code in (0, 1)
        # Either shows help or reports no input
        assert ("TTT - Text-to-Text Processing Library" in result.output or 
                "No input provided" in result.output)

    def test_tools_parsing(self):
        """Test tools argument parsing."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, [
                "Calculate 2+2",
                "--tools", "math:add,calculate"
            ])
            
            assert result.exit_code == 0
            # The tools should be passed to the ask function
            mock_ask.assert_called_once()


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_full_ask_flow(self):
        """Test the complete ask flow."""
        with patch('ai.ask') as mock_ask:
            # Mock response
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "AI response"
            mock_response.model = "test-model"
            mock_response.backend = "cloud" 
            mock_response.time = 1.23
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ["What is 2+2?"])
            
            assert result.exit_code == 0
            mock_ask.assert_called_once()
            
            # Verify the call parameters
            call_args = mock_ask.call_args
            assert call_args[0][0] == "What is 2+2?"  # prompt

    def test_no_backend_available(self):
        """Test behavior when no backend is available."""
        with patch('ai.ask') as mock_ask:
            # Simulate backend not available error
            from ai.exceptions import BackendNotAvailableError
            mock_ask.side_effect = BackendNotAvailableError("local", "No backends available")
            
            result = self.runner.invoke(main, ["test"])
            
            # Should exit with error
            assert result.exit_code == 1
            assert "not available" in result.output.lower()

    def test_auto_coding_detection(self):
        """Test that coding-related prompts work."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "response"
            mock_response.model = "gpt-4"
            mock_response.backend = "cloud"
            mock_response.time = 1.23
            mock_response.tokens_in = 10
            mock_response.tokens_out = 20
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ["write a function", "--verbose"])
            
            assert result.exit_code == 0
            mock_ask.assert_called_once()
            # Check that the prompt was processed
            call_args = mock_ask.call_args
            assert call_args[0][0] == "write a function"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])