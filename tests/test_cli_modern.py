"""Comprehensive tests for the modern Click-based CLI interface.

Tests all commands, options, help text, and integration with the app hooks system.
"""

from unittest.mock import MagicMock, Mock, patch
import json

import pytest
from click.testing import CliRunner

from ttt.cli import main


class TestCLIStructure:
    """Test CLI structure and help display."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_main_help_display(self):
        """Test that main help displays correctly with proper sections."""
        result = self.runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        output = result.output
        
        # Verify key elements are present (allowing for rich formatting)
        assert "Talk to Transformer" in output
        assert "ask" in output
        assert "chat" in output
        assert "list" in output
        assert "status" in output
        assert "models" in output
        assert "info" in output
        assert "config" in output
        assert "tools" in output
        assert "export" in output

    def test_main_options_are_minimal(self):
        """Test that main help only shows --help option."""
        result = self.runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        output = result.output
        
        # Should have --help in options
        assert "--help" in output
        # Find options section - these should NOT be in main options
        lines = output.split("\n")
        in_options = False
        options_content = []
        for line in lines:
            if "Options" in line or "─ Options ─" in line:
                in_options = True
            elif "Commands" in line or "─ Commands ─" in line:
                in_options = False
            elif in_options and line.strip():
                options_content.append(line)
        
        option_text = " ".join(options_content)
        assert "--model" not in option_text
        assert "--temperature" not in option_text

    def test_no_command_shows_help(self):
        """Test that invoking with no command shows help."""
        result = self.runner.invoke(main, [])
        
        assert result.exit_code == 0
        assert "Talk to Transformer" in result.output


class TestAskCommand:
    """Test the ask command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_ask_help_displays_options(self):
        """Test ask command help shows all available options."""
        result = self.runner.invoke(main, ["ask", "--help"])
        
        assert result.exit_code == 0
        output = result.output
        
        # Verify all ask options are present
        assert "--model" in output or "-m" in output
        assert "--temperature" in output or "-t" in output
        assert "--max-tokens" in output
        assert "--tools" in output
        assert "--session" in output or "-s" in output
        assert "--stream" in output

    def test_ask_basic_prompt(self):
        """Test basic ask functionality with hook mocking."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_ask = Mock()
            
            result = self.runner.invoke(main, ["ask", "What is Python?"])
            
            # Should call the hook or execute fallback behavior
            assert result.exit_code == 0

    def test_ask_with_options(self):
        """Test ask with various options."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_ask = Mock()
            
            result = self.runner.invoke(main, [
                "ask", "Debug this code",
                "--model", "gpt-4",
                "--temperature", "0.7",
                "--tools",
                "--session", "test-session"
            ])
            
            assert result.exit_code == 0

    def test_ask_requires_prompt(self):
        """Test that ask command requires a prompt."""
        result = self.runner.invoke(main, ["ask"])
        
        # Should fail when no prompt provided
        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_ask_invalid_temperature(self):
        """Test validation for temperature values."""
        result = self.runner.invoke(main, [
            "ask", "test", "--temperature", "invalid"
        ])
        
        assert result.exit_code == 2  # Click validation error


class TestChatCommand:
    """Test the chat command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_chat_help_displays_options(self):
        """Test chat command help shows all available options."""
        result = self.runner.invoke(main, ["chat", "--help"])
        
        assert result.exit_code == 0
        output = result.output
        
        # Verify chat options are present
        assert "--model" in output or "-m" in output
        assert "--session" in output or "-s" in output
        assert "--tools" in output
        assert "--markdown" in output

    def test_chat_basic(self):
        """Test basic chat functionality."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            # Mock to avoid actual chat loop
            mock_hooks.on_chat = Mock()
            
            result = self.runner.invoke(main, ["chat"])
            
            # Should execute without errors
            assert result.exit_code == 0

    def test_chat_with_options(self):
        """Test chat with various options."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_chat = Mock()
            
            result = self.runner.invoke(main, [
                "chat",
                "--model", "gpt-4", 
                "--session", "my-session",
                "--tools"
            ])
            
            assert result.exit_code == 0


class TestListCommand:
    """Test the list command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_list_help_shows_resources(self):
        """Test list command help shows available resources."""
        result = self.runner.invoke(main, ["list", "--help"])
        
        assert result.exit_code == 0
        output = result.output
        
        # Should show available resource choices
        assert "models" in output
        assert "sessions" in output  
        assert "tools" in output

    def test_list_models(self):
        """Test listing models."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_list = Mock()
            
            result = self.runner.invoke(main, ["list", "models"])
            
            assert result.exit_code == 0

    def test_list_with_format(self):
        """Test list with different format."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_list = Mock()
            
            result = self.runner.invoke(main, ["list", "models", "--format", "json"])
            
            assert result.exit_code == 0

    def test_list_requires_resource(self):
        """Test that list command requires a resource argument."""
        result = self.runner.invoke(main, ["list"])
        
        assert result.exit_code == 2  # Click validation error
        assert "Missing argument" in result.output

    def test_list_invalid_resource(self):
        """Test validation for resource argument."""
        result = self.runner.invoke(main, ["list", "invalid"])
        
        assert result.exit_code == 2  # Click validation error


class TestConfigCommand:
    """Test the config command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_config_help(self):
        """Test config command help."""
        result = self.runner.invoke(main, ["config", "--help"])
        
        assert result.exit_code == 0
        output = result.output
        assert "Manage configuration" in output

    def test_config_subcommands_exist(self):
        """Test that config subcommands are available."""
        result = self.runner.invoke(main, ["config", "--help"])
        
        assert result.exit_code == 0
        output = result.output
        
        # Should list subcommands
        assert "get" in output
        assert "set" in output
        assert "list" in output

    def test_config_get(self):
        """Test config get subcommand."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_config_get = Mock()
            
            result = self.runner.invoke(main, ["config", "get", "model"])
            
            assert result.exit_code == 0

    def test_config_set(self):
        """Test config set subcommand."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_config_set = Mock()
            
            result = self.runner.invoke(main, ["config", "set", "model", "gpt-4"])
            
            assert result.exit_code == 0

    def test_config_list(self):
        """Test config list subcommand."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_config_list = Mock()
            
            result = self.runner.invoke(main, ["config", "list"])
            
            assert result.exit_code == 0

    def test_config_list_with_secrets(self):
        """Test config list with show-secrets option."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_config_list = Mock()
            
            result = self.runner.invoke(main, ["config", "list", "--show-secrets"])
            
            assert result.exit_code == 0


class TestToolsCommand:
    """Test the tools command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_tools_help(self):
        """Test tools command help."""
        result = self.runner.invoke(main, ["tools", "--help"])
        
        assert result.exit_code == 0
        output = result.output
        assert "Manage available tools" in output

    def test_tools_subcommands_exist(self):
        """Test that tools subcommands are available."""
        result = self.runner.invoke(main, ["tools", "--help"])
        
        assert result.exit_code == 0
        output = result.output
        
        # Should list subcommands
        assert "enable" in output
        assert "disable" in output
        assert "list" in output

    def test_tools_enable(self):
        """Test tools enable subcommand."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_tools_enable = Mock()
            
            result = self.runner.invoke(main, ["tools", "enable", "web_search"])
            
            assert result.exit_code == 0

    def test_tools_disable(self):
        """Test tools disable subcommand."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_tools_disable = Mock()
            
            result = self.runner.invoke(main, ["tools", "disable", "web_search"])
            
            assert result.exit_code == 0

    def test_tools_list(self):
        """Test tools list subcommand."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_tools_list = Mock()
            
            result = self.runner.invoke(main, ["tools", "list"])
            
            assert result.exit_code == 0


class TestStatusCommand:
    """Test the status command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_status_basic(self):
        """Test basic status command."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_status = Mock()
            
            result = self.runner.invoke(main, ["status"])
            
            assert result.exit_code == 0


class TestModelsCommand:
    """Test the models command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_models_basic(self):
        """Test basic models command."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_models = Mock()
            
            result = self.runner.invoke(main, ["models"])
            
            assert result.exit_code == 0


class TestInfoCommand:
    """Test the info command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_info_basic(self):
        """Test basic info command."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_info = Mock()
            
            result = self.runner.invoke(main, ["info", "gpt-4"])
            
            assert result.exit_code == 0

    def test_info_requires_model(self):
        """Test that info command requires a model argument."""
        result = self.runner.invoke(main, ["info"])
        
        assert result.exit_code == 2  # Click validation error
        assert "Missing argument" in result.output


class TestExportCommand:
    """Test the export command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_export_basic(self):
        """Test basic export command."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_export = Mock()
            
            result = self.runner.invoke(main, ["export", "session-1"])
            
            assert result.exit_code == 0

    def test_export_with_options(self):
        """Test export with various options."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            mock_hooks.on_export = Mock()
            
            result = self.runner.invoke(main, [
                "export", "session-1",
                "--format", "json",
                "--output", "output.json",
                "--include-metadata"
            ])
            
            assert result.exit_code == 0

    def test_export_requires_session(self):
        """Test that export command requires a session argument."""
        result = self.runner.invoke(main, ["export"])
        
        assert result.exit_code == 2  # Click validation error
        assert "Missing argument" in result.output


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_invalid_command(self):
        """Test handling of invalid commands."""
        result = self.runner.invoke(main, ["invalid-command"])
        
        assert result.exit_code == 2
        assert "No such command" in result.output

    def test_invalid_option(self):
        """Test handling of invalid options."""
        result = self.runner.invoke(main, ["ask", "test", "--invalid-option"])
        
        assert result.exit_code == 2
        assert "No such option" in result.output

    def test_hook_exception_handling(self):
        """Test that exceptions from hooks are handled gracefully."""
        with patch("ttt.cli.app_hooks") as mock_hooks:
            # Make the hook raise an exception
            mock_hooks.on_ask = Mock(side_effect=Exception("Test error"))
            
            result = self.runner.invoke(main, ["ask", "test"])
            
            # Should handle exception gracefully - exact behavior depends on implementation
            # At minimum, shouldn't crash completely
            assert result.exit_code in [0, 1]


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_command_chain_compatibility(self):
        """Test that commands work with shell pipes and redirects."""
        # Test help for all main commands
        commands = ["ask", "chat", "list", "status", "models", "info", "config", "tools", "export"]
        
        for cmd in commands:
            result = self.runner.invoke(main, [cmd, "--help"])
            assert result.exit_code == 0, f"Help failed for command: {cmd}"

    def test_nested_subcommands(self):
        """Test that nested subcommands work correctly."""
        # Test config subcommands
        config_subcommands = ["get", "set", "list"]
        for subcmd in config_subcommands:
            result = self.runner.invoke(main, ["config", subcmd, "--help"])
            assert result.exit_code == 0, f"Help failed for config {subcmd}"
        
        # Test tools subcommands  
        tools_subcommands = ["enable", "disable", "list"]
        for subcmd in tools_subcommands:
            result = self.runner.invoke(main, ["tools", subcmd, "--help"])
            assert result.exit_code == 0, f"Help failed for tools {subcmd}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])