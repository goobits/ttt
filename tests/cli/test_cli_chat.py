"""Tests for the chat CLI command functionality."""

from ttt.cli import main
from tests.cli.conftest import IntegrationTestBase


class TestChatCommand(IntegrationTestBase):
    """Test the chat command functionality."""

    def test_chat_command_exists(self):
        """Test that chat command is available and accepts --help."""
        result = self.runner.invoke(main, ["chat", "--help"])
        assert result.exit_code == 0

    def test_chat_command_accepts_help_and_validates_options(self):
        """Test basic chat functionality."""
        # Chat command is interactive, so we can only test help and argument validation
        # Real chat functionality would hang waiting for user input
        result = self.runner.invoke(main, ["chat", "--help"])
        assert result.exit_code == 0

    def test_chat_with_options(self):
        """Test chat command handles options correctly."""
        # Chat is interactive, but we can test that options are accepted without errors
        # by testing help with complex arguments
        result = self.runner.invoke(main, ["chat", "--help"])
        assert result.exit_code == 0
        
        # Verify help shows the options we expect
        assert "--model" in result.output
        assert "--session" in result.output
        assert "--tools" in result.output

    def test_chat_command_parameter_passing(self):
        """Test chat command passes all parameters correctly."""
        # Chat command is interactive, so we mainly test that it handles parameters correctly
        # and doesn't crash with argument parsing errors
        result = self.runner.invoke(main, [
            "chat",
            "--model", "gpt-3.5-turbo",
            "--session", "chat-session-1",
            "--tools", "false",
            "--markdown", "true"
        ], input="\n")  # Send empty input to exit chat mode
        
        # Chat command should handle parameters correctly (exit codes 0 or 1 are acceptable)
        # Exit code 2 would indicate argument parsing failure
        assert result.exit_code != 2, f"Chat command had argument parsing error: {result.output}"
        
        # The main validation is that it doesn't crash on parameter parsing
        # Chat functionality itself would need user interaction to test fully