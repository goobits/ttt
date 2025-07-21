"""CLI verification tests based on TTT_CLI.md checklist.

This test suite focuses on verifying the CLI structure and command availability.
It ensures the TTT CLI maintains its professional structure with proper option scoping.
"""

import os
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from ttt.cli import main


class TestCLIVerification:
    """Verify CLI commands work as documented."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    # ===== CLI STRUCTURE TESTS =====

    def test_help_command(self):
        """Verify help displays correctly with clean structure."""
        result = self.runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        output = result.output
        
        # Verify main help is clean (only --version and --help in options)
        assert "--version" in output
        assert "--help" in output
        
        # These should NOT be in main help options
        lines = output.split("\n")
        in_options = False
        for line in lines:
            if "Options" in line:
                in_options = True
            elif "Commands" in line:
                in_options = False
            
            if in_options and "--model" in line:
                pytest.fail("--model should not be in main options")

        # Verify sections exist
        assert "Core Commands:" in output
        assert "Model Management:" in output

    def test_ask_help(self):
        """Verify ask command has all options."""
        result = self.runner.invoke(main, ["ask", "--help"])
        
        assert result.exit_code == 0
        output = result.output
        
        # All options should be present
        assert "--model" in output
        assert "--temperature" in output
        assert "--system" in output
        assert "--max-tokens" in output
        assert "--tools" in output
        assert "--stream" in output
        assert "--json" in output
        assert "--verbose" in output
        assert "--debug" in output
        assert "--code" in output

    # ===== COMMAND AVAILABILITY TESTS =====

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

    # ===== CONFIG TESTS =====

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

    # ===== ERROR HANDLING TESTS =====

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


class TestCLIStructureVerification:
    """Verify the CLI structure matches design requirements."""

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

    def test_subcommands_have_options(self):
        """Verify subcommands have the operational options."""
        # Check ask command
        result = self.runner.invoke(main, ["ask", "--help"])
        assert result.exit_code == 0
        ask_output = result.output
        
        assert "--model" in ask_output
        assert "--temperature" in ask_output
        assert "--system" in ask_output
        assert "--json" in ask_output
        
        # Check chat command  
        result = self.runner.invoke(main, ["chat", "--help"])
        assert result.exit_code == 0
        chat_output = result.output
        
        assert "--model" in chat_output
        assert "--resume" in chat_output
        assert "--list" in chat_output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])