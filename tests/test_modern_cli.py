"""Modern CLI tests using Typer's testing facilities."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from ai.cli import app


class TestTyperCLI:
    """Test the refactored Typer-based CLI."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_ask_command_basic(self):
        """Test basic ask command functionality."""
        with patch('ai.cli._handle_query') as mock_handle:
            result = self.runner.invoke(app, ["ask", "What is Python?"])
            
            assert result.exit_code == 0
            mock_handle.assert_called_once()
            # Check that the arguments were parsed correctly
            args = mock_handle.call_args[0][0]
            assert args["prompt"] == "What is Python?"
            assert args["command"] == "query"

    def test_ask_command_with_options(self):
        """Test ask command with various options."""
        with patch('ai.cli._handle_query') as mock_handle:
            result = self.runner.invoke(app, [
                "ask", "Debug this code",
                "--model", "gpt-4",
                "--backend", "cloud",
                "--temperature", "0.7",
                "--verbose",
                "--code"
            ])
            
            assert result.exit_code == 0
            args = mock_handle.call_args[0][0]
            assert args["prompt"] == "Debug this code"
            assert args["model"] == "gpt-4"
            assert args["backend"] == "cloud"
            assert args["temperature"] == 0.7
            assert args["verbose"] is True
            assert args["code"] is True

    def test_ask_command_with_shortcuts(self):
        """Test ask command with offline/online shortcuts."""
        with patch('ai.cli._handle_query') as mock_handle:
            # Test offline shortcut
            result = self.runner.invoke(app, ["ask", "test", "--offline"])
            assert result.exit_code == 0
            args = mock_handle.call_args[0][0]
            assert args["backend"] == "local"
            assert args["offline"] is True

            # Test online shortcut
            result = self.runner.invoke(app, ["ask", "test", "--online"])
            assert result.exit_code == 0
            args = mock_handle.call_args[0][0]
            assert args["backend"] == "cloud"
            assert args["online"] is True

    def test_ask_command_stdin(self):
        """Test ask command with stdin input."""
        with patch('ai.cli._handle_query') as mock_handle:
            with patch('sys.stdin.read', return_value="Input from stdin"):
                result = self.runner.invoke(app, ["ask", "-"])
                
                assert result.exit_code == 0
                args = mock_handle.call_args[0][0]
                assert args["prompt"] == "Input from stdin"

    def test_chat_command(self):
        """Test chat command."""
        with patch('ai.cli.handle_interactive_chat', return_value=None) as mock_chat:
            result = self.runner.invoke(app, [
                "chat",
                "--model", "claude-3-sonnet",
                "--system", "You are helpful",
                "--verbose"
            ])
            
            assert result.exit_code == 0
            mock_chat.assert_called_once()
            args = mock_chat.call_args[0][0]
            assert args["model"] == "claude-3-sonnet"
            assert args["system"] == "You are helpful"
            assert args["verbose"] is True

    def test_backend_status_command(self):
        """Test backend-status command."""
        with patch('ai.cli.show_backend_status') as mock_status:
            result = self.runner.invoke(app, ["backend-status"])
            
            assert result.exit_code == 0
            mock_status.assert_called_once()

    def test_models_list_command(self):
        """Test models-list command."""
        with patch('ai.cli.show_models_list') as mock_models:
            result = self.runner.invoke(app, ["models-list"])
            
            assert result.exit_code == 0
            mock_models.assert_called_once()

    def test_tools_list_command(self):
        """Test tools-list command."""
        with patch('ai.cli.show_tools_list') as mock_tools:
            result = self.runner.invoke(app, ["tools-list"])
            
            assert result.exit_code == 0
            mock_tools.assert_called_once()

    def test_help_display(self):
        """Test that help is displayed correctly."""
        result = self.runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "AI Library - Unified AI Interface" in result.stdout
        assert "ask" in result.stdout
        assert "chat" in result.stdout

    def test_command_help(self):
        """Test individual command help."""
        result = self.runner.invoke(app, ["ask", "--help"])
        
        assert result.exit_code == 0
        assert "Ask the AI a question" in result.stdout
        assert "--model" in result.stdout
        assert "--backend" in result.stdout

    def test_invalid_arguments(self):
        """Test handling of invalid arguments."""
        # Missing required prompt argument
        result = self.runner.invoke(app, ["ask"])
        assert result.exit_code != 0
        assert "Missing argument" in result.stdout

    def test_tools_parsing(self):
        """Test tools argument parsing."""
        with patch('ai.cli._handle_query') as mock_handle:
            result = self.runner.invoke(app, [
                "ask", "Calculate 2+2",
                "--tools", "math:add,calculate"
            ])
            
            assert result.exit_code == 0
            args = mock_handle.call_args[0][0]
            assert args["tools"] == ["math:add", "calculate"]


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('ai.cli.check_backend_available', return_value=True)
    @patch('ai.cli.detect_best_backend', return_value='cloud')
    @patch('ai.api.ask')
    def test_full_ask_flow(self, mock_ask, mock_detect, mock_check):
        """Test the complete ask flow."""
        # Mock response
        mock_response = MagicMock()
        mock_response.__str__ = lambda x: "AI response"
        mock_response.model = "test-model"
        mock_response.backend = "cloud" 
        mock_response.time = 1.23
        mock_ask.return_value = mock_response

        result = self.runner.invoke(app, ["ask", "What is 2+2?"])
        
        assert result.exit_code == 0
        mock_ask.assert_called_once()
        
        # Verify the call parameters
        call_args = mock_ask.call_args
        assert call_args[0][0] == "What is 2+2?"  # prompt
        assert "backend" in call_args[1]

    @patch('ai.cli.check_backend_available', return_value=False)
    @patch('ai.cli.show_setup_guidance')
    def test_no_backend_available(self, mock_guidance, mock_check):
        """Test behavior when no backend is available."""
        result = self.runner.invoke(app, ["ask", "test"])
        
        # Should not exit with error, but should show guidance
        mock_guidance.assert_called_once()

    @patch('ai.cli.is_coding_request', return_value=True)
    @patch('ai.cli.apply_coding_optimization')
    @patch('ai.cli.check_backend_available', return_value=True)
    @patch('ai.api.ask')
    def test_auto_coding_detection(self, mock_ask, mock_check, mock_optimize, mock_detect):
        """Test automatic coding request detection."""
        mock_ask.return_value = MagicMock(__str__=lambda x: "response")
        mock_optimize.return_value = {"temperature": 0.3}
        
        result = self.runner.invoke(app, ["ask", "write a function", "--verbose"])
        
        assert result.exit_code == 0
        mock_detect.assert_called_with("write a function")
        mock_optimize.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])