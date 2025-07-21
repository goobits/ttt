"""CLI interface tests combining structure verification and integration testing.

This test suite verifies the CLI interface structure, command availability, and functionality.
It ensures the TTT CLI maintains its professional structure with proper option scoping.
"""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from ttt.cli import main


class TestCLIStructure:
    """Test CLI structure and help display."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_main_help_is_clean(self):
        """Verify main help only has --version and --help."""
        result = self.runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        output = result.output
        
        # Find the Options section
        lines = output.split("\n")
        options_content = []
        in_options = False
        
        for line in lines:
            if "Options" in line or "─ Options ─" in line:
                in_options = True
                continue
            elif ("Commands" in line or "─ Commands ─" in line or 
                  line.startswith("╰")):
                in_options = False
            elif in_options and line.strip():
                options_content.append(line)
        
        # Only --version and --help should be in main options
        option_text = " ".join(options_content)
        assert "--version" in option_text
        assert "--help" in option_text
        
        # These should NOT be there
        assert "--model" not in option_text
        assert "--temperature" not in option_text
        assert "--stream" not in option_text

    def test_help_structure(self):
        """Verify help displays correctly with clean structure."""
        result = self.runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        output = result.output
        
        # Verify main sections exist
        assert "TTT - Text-to-Text Processing Library" in output
        assert "--version" in output
        assert "--help" in output

    def test_subcommands_have_options(self):
        """Verify subcommands have the operational options."""
        # Check ask command
        result = self.runner.invoke(main, ["ask", "--help"])
        assert result.exit_code == 0
        ask_output = result.output
        
        assert "--model" in ask_output
        assert "--temperature" in ask_output
        assert "--system" in ask_output
        assert "--max-tokens" in ask_output
        assert "--tools" in ask_output
        assert "--stream" in ask_output
        assert "--json" in ask_output
        assert "--verbose" in ask_output
        assert "--debug" in ask_output
        assert "--code" in ask_output
        
        # Check chat command  
        result = self.runner.invoke(main, ["chat", "--help"])
        assert result.exit_code == 0
        chat_output = result.output
        
        assert "--model" in chat_output
        assert "--resume" in chat_output
        assert "--list" in chat_output


class TestCLICommands:
    """Test CLI command availability and functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("ttt.cli.show_backend_status")
    def test_status_command(self, mock_status):
        """Verify: ttt status"""
        result = self.runner.invoke(main, ["status"])
        
        assert result.exit_code == 0
        mock_status.assert_called_once_with(False)

    @patch("ttt.cli.show_backend_status")
    def test_status_json(self, mock_status):
        """Verify: ttt status --json"""
        result = self.runner.invoke(main, ["status", "--json"])
        
        assert result.exit_code == 0
        mock_status.assert_called_once_with(True)

    @patch("ttt.cli.show_models_list")
    def test_models_command(self, mock_models):
        """Verify: ttt models"""
        result = self.runner.invoke(main, ["models"])
        
        assert result.exit_code == 0
        mock_models.assert_called_once_with(False)

    @patch("ttt.cli.show_model_info")
    def test_info_command(self, mock_info):
        """Verify: ttt info gpt-4"""
        result = self.runner.invoke(main, ["info", "gpt-4"])
        
        assert result.exit_code == 0
        mock_info.assert_called_once_with("gpt-4", False)

    def test_config_help(self):
        """Verify config command has examples."""
        result = self.runner.invoke(main, ["config", "--help"])
        
        assert result.exit_code == 0
        output = result.output
        assert "ttt config set openrouter_api_key YOUR_KEY" in output

    @patch("ttt.config_manager.ConfigManager")
    def test_config_set_api_key(self, mock_config_manager):
        """Verify: ttt config set openrouter_api_key KEY"""
        mock_instance = Mock()
        mock_config_manager.return_value = mock_instance
        
        result = self.runner.invoke(main, [
            "config", "set", "openrouter_api_key", "test-key"
        ])
        
        assert result.exit_code == 0
        mock_instance.set_value.assert_called_once_with(
            "openrouter_api_key", "test-key"
        )


class TestCLIFunctionality:
    """Test CLI functionality with mocked backends."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_direct_prompt_basic(self):
        """Test basic direct prompt functionality."""
        with patch("ttt.ask") as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ["ask", "What is Python?"])

            assert result.exit_code == 0
            mock_ask.assert_called_once()
            call_args = mock_ask.call_args
            assert call_args[0][0] == "What is Python?"

    def test_direct_prompt_with_options(self):
        """Test direct prompt with various options."""
        with patch("ttt.ask") as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_response.model = "gpt-4"
            mock_response.backend = "cloud"
            mock_response.time = 1.23
            mock_response.tokens_in = 10
            mock_response.tokens_out = 20
            mock_ask.return_value = mock_response

            result = self.runner.invoke(
                main,
                [
                    "ask",
                    "Debug this code",
                    "--model",
                    "gpt-4",
                    "--temperature",
                    "0.7",
                    "--verbose",
                    "--code",
                ],
            )

            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs["model"] == "gpt-4"
            assert call_kwargs["temperature"] == 0.7

    def test_chat_command(self):
        """Test chat command."""
        with patch("ttt.chat") as mock_chat_context:
            mock_session = Mock()
            mock_chat_context.return_value.__enter__ = lambda x: mock_session
            mock_chat_context.return_value.__exit__ = lambda x, *args: None

            # Simulate immediate exit from chat
            with patch("click.prompt", side_effect=EOFError):
                result = self.runner.invoke(
                    main,
                    [
                        "chat",
                        "--model",
                        "claude-3-sonnet",
                        "--system",
                        "You are helpful",
                        "--verbose",
                    ],
                )

            assert result.exit_code == 0
            mock_chat_context.assert_called_once()

    def test_tools_parsing(self):
        """Test tools argument parsing."""
        with patch("ttt.ask") as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response

            result = self.runner.invoke(
                main, ["ask", "Calculate 2+2", "--tools", "math:add,calculate"]
            )

            assert result.exit_code == 0
            # The tools should be passed to the ask function
            mock_ask.assert_called_once()

    def test_no_backend_available(self):
        """Test behavior when no backend is available."""
        with patch("ttt.ask") as mock_ask:
            # Simulate backend not available error
            from ttt.exceptions import BackendNotAvailableError

            mock_ask.side_effect = BackendNotAvailableError(
                "local", "No backends available"
            )

            result = self.runner.invoke(main, ["ask", "test"])

            # Should exit with error
            assert result.exit_code == 1
            assert "not available" in result.output.lower()

    def test_full_ask_flow(self):
        """Test the complete ask flow."""
        with patch("ttt.ask") as mock_ask:
            # Mock response
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "AI response"
            mock_response.model = "test-model"
            mock_response.backend = "cloud"
            mock_response.time = 1.23
            mock_ask.return_value = mock_response

            result = self.runner.invoke(main, ["ask", "What is 2+2?"])

            assert result.exit_code == 0
            mock_ask.assert_called_once()

            # Verify the call parameters
            call_args = mock_ask.call_args
            assert call_args[0][0] == "What is 2+2?"  # prompt


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_invalid_command(self):
        """Verify proper error for invalid command."""
        result = self.runner.invoke(main, ["invalid-command"])
        
        assert result.exit_code == 2
        assert "No such command" in result.output or "Error" in result.output

    def test_invalid_temperature(self):
        """Verify validation for temperature values."""
        result = self.runner.invoke(main, [
            "ask", "--temperature", "invalid", "test"
        ])
        
        assert result.exit_code == 2  # Click validation error

    def test_no_arguments(self):
        """Test handling when no arguments provided."""
        result = self.runner.invoke(main, [])
        assert result.exit_code in (0, 1)
        # Either shows help or reports no input
        assert (
            "TTT - Text-to-Text Processing Library" in result.output
            or "No input provided" in result.output
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])