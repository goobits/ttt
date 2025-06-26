"""Tests for configurable tool settings."""

import pytest
from unittest.mock import patch, Mock
import tempfile
import os

from ai.tools.builtins import _get_max_file_size, _get_code_timeout, _get_web_timeout
from ai.config import load_config


class TestConfigurableTools:
    """Test that tools respect configuration settings."""

    def test_default_tool_config(self):
        """Test that tools use default values when no config is provided."""
        # Should use default values
        assert _get_max_file_size() == 10 * 1024 * 1024  # 10MB
        assert _get_code_timeout() == 30
        assert _get_web_timeout() == 10

    def test_custom_tool_config(self):
        """Test that tools use custom configuration values."""
        # Create a custom config
        custom_config = {
            "tools": {
                "max_file_size": 5 * 1024 * 1024,  # 5MB
                "code_execution_timeout": 15,
                "web_request_timeout": 5,
            }
        }

        with patch("ai.config.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.config_data = custom_config
            mock_get_config.return_value = mock_config

            # Should use custom values
            assert _get_max_file_size() == 5 * 1024 * 1024  # 5MB
            assert _get_code_timeout() == 15
            assert _get_web_timeout() == 5

    def test_read_file_respects_config(self):
        """Test that read_file tool respects max_file_size config."""
        from ai.tools.builtins import read_file

        # Create a temporary file larger than custom limit
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            # Write 6MB of data
            f.write("x" * (6 * 1024 * 1024))
            temp_path = f.name

        try:
            # Mock config with 5MB limit
            custom_config = {"tools": {"max_file_size": 5 * 1024 * 1024}}  # 5MB

            with patch("ai.config.get_config") as mock_get_config:
                mock_config = Mock()
                mock_config.config_data = custom_config
                mock_get_config.return_value = mock_config

                # Should fail due to size limit
                result = read_file(temp_path)
                assert "Error: File too large" in result
                assert "5242880 bytes" in result  # 5MB in bytes

        finally:
            os.unlink(temp_path)

    def test_run_python_respects_timeout_config(self):
        """Test that run_python tool respects timeout config."""
        from ai.tools.builtins import run_python

        # Mock config with shorter timeout
        custom_config = {"tools": {"code_execution_timeout": 1}}  # 1 second

        with patch("ai.config.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.config_data = custom_config
            mock_get_config.return_value = mock_config

            # Code that would normally take longer than 1 second
            code = """
import time
time.sleep(2)
print("This should timeout")
"""

            result = run_python(code)
            # Should timeout or show error
            assert any(keyword in result.lower() for keyword in ["timeout", "error"])


class TestToolsListCommand:
    """Test the tools-list CLI command."""

    def test_tools_list_command_parsing(self):
        """Test that tools-list command is parsed correctly."""
        from ai.cli import parse_args

        with patch("sys.argv", ["ai", "tools-list"]):
            args = parse_args()
            assert args["command"] == "tools-list"

        # Test alias
        with patch("sys.argv", ["ai", "tools"]):
            args = parse_args()
            assert args["command"] == "tools-list"

    @patch("ai.cli.console")
    def test_show_tools_list(self, mock_console):
        """Test the show_tools_list function."""
        from ai.cli import show_tools_list

        # Mock the tools registry
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"
        mock_tool.category = "test"

        with patch("ai.cli.list_tools", return_value=[mock_tool]):
            show_tools_list()

            # Should have called console.print with tool information
            mock_console.print.assert_called()
            print_calls = [str(call) for call in mock_console.print.call_args_list]

            # Check that tool info was displayed
            assert any("test_tool" in call for call in print_calls)
            assert any("Test Tools:" in call for call in print_calls)


if __name__ == "__main__":
    pytest.main([__file__])
