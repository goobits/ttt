"""Tests for CLI functionality using modern Click testing patterns."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai.cli import main, is_coding_request, apply_coding_optimization


class TestCLICommands:
    """Test CLI commands using Click CliRunner."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_basic_ask_command(self):
        """Test basic ask command functionality."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_response.model = "test-model"
            mock_response.backend = "test"
            mock_response.time = 1.23
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ['ask', 'What is Python?'])
            
            assert result.exit_code == 0
            mock_ask.assert_called_once()
            call_args = mock_ask.call_args
            assert call_args[0][0] == 'What is Python?'

    def test_ask_with_model_option(self):
        """Test ask command with model option."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ['ask', 'Test prompt', '--model', 'gpt-4'])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs['model'] == 'gpt-4'


    def test_ask_with_temperature(self):
        """Test ask command with temperature option."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ['ask', 'Test prompt', '--temperature', '0.7'])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs['temperature'] == 0.7

    def test_ask_with_offline_shortcut(self):
        """Test ask command with offline shortcut."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ['ask', 'Test prompt', '--offline'])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs['backend'] == 'local'

    def test_ask_with_online_shortcut(self):
        """Test ask command with online shortcut."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ['ask', 'Test prompt', '--online'])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs['backend'] == 'cloud'

    def test_ask_with_backend_override(self):
        """Test ask command with backend override."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ['ask', 'Test', '--offline'])
            
            assert result.exit_code == 0
            call_kwargs = mock_ask.call_args[1]
            assert call_kwargs['backend'] == 'local'

    def test_ask_with_streaming(self):
        """Test ask command with streaming."""
        with patch('ai.stream') as mock_stream:
            mock_stream.return_value = iter(['chunk1', 'chunk2', 'chunk3'])
            
            result = self.runner.invoke(main, ['ask', 'Test prompt', '--stream'])
            
            assert result.exit_code == 0
            mock_stream.assert_called_once()
            assert 'chunk1chunk2chunk3' in result.output

    def test_chat_command(self):
        """Test chat command initialization."""
        with patch('ai.chat') as mock_chat_context:
            mock_session = MagicMock()
            mock_chat_context.return_value.__enter__ = lambda x: mock_session
            mock_chat_context.return_value.__exit__ = lambda x, *args: None
            
            # Simulate immediate exit
            with patch('click.prompt', side_effect=EOFError):
                result = self.runner.invoke(main, ['chat'])
            
            assert result.exit_code == 0
            mock_chat_context.assert_called_once()

    def test_backend_status_command(self):
        """Test status command."""
        with patch('ai.cli.show_backend_status') as mock_status:
            result = self.runner.invoke(main, ['status'])
            
            assert result.exit_code == 0
            mock_status.assert_called_once()

    def test_models_list_command(self):
        """Test models command."""
        with patch('ai.cli.show_models_list') as mock_models:
            result = self.runner.invoke(main, ['models'])
            
            assert result.exit_code == 0
            mock_models.assert_called_once()

    def test_tools_list_command(self):
        """Test tools command."""
        with patch('ai.cli.show_tools_list') as mock_tools:
            result = self.runner.invoke(main, ['tools'])
            
            assert result.exit_code == 0
            mock_tools.assert_called_once()

    def test_help_display(self):
        """Test help display."""
        result = self.runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert 'AI Library - Unified AI Interface' in result.output

    def test_version_display(self):
        """Test version display."""
        result = self.runner.invoke(main, ['--version'])
        
        assert result.exit_code == 0
        assert 'AI Library v' in result.output


class TestHelperFunctions:
    """Test CLI helper functions."""


    def test_is_coding_request(self):
        """Test coding request detection."""
        assert is_coding_request("write a function") is True
        assert is_coding_request("debug this code") is True
        assert is_coding_request("what is the weather") is False

    def test_apply_coding_optimization(self):
        """Test coding optimization application."""
        kwargs = {}
        apply_coding_optimization(kwargs)
        
        # Should only set temperature for code optimization
        assert kwargs['temperature'] == 0.3



class TestErrorHandling:
    """Test error handling in CLI."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_missing_prompt(self):
        """Test handling of missing prompt argument."""
        # With new CLI, missing prompt should show help, not error
        result = self.runner.invoke(main, [])
        
        # Should either show help (exit 0) or report no input (exit 1)
        assert result.exit_code in (0, 1)
        assert ('AI Library' in result.output or 'No input provided' in result.output)

    def test_invalid_temperature(self):
        """Test handling of invalid temperature value."""
        with patch('ai.ask') as mock_ask:
            mock_ask.side_effect = ValueError("Invalid temperature")
            
            result = self.runner.invoke(main, ['ask', 'test', '--temperature', '2.0'])
            
            assert result.exit_code == 1
            assert 'Error:' in result.output

    def test_api_error_handling(self):
        """Test handling of API errors."""
        with patch('ai.ask') as mock_ask:
            mock_ask.side_effect = Exception("API Error")
            
            result = self.runner.invoke(main, ['ask', 'test'])
            
            assert result.exit_code == 1
            assert 'Error: API Error' in result.output


class TestStdinInput:
    """Test stdin input handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_stdin_input(self):
        """Test reading from stdin."""
        with patch('ai.ask') as mock_ask:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Mock response"
            mock_ask.return_value = mock_response
            
            result = self.runner.invoke(main, ['ask', '-'], input='stdin input')
            
            assert result.exit_code == 0
            call_args = mock_ask.call_args
            assert call_args[0][0] == 'stdin input'

    def test_empty_stdin(self):
        """Test handling of empty stdin."""
        result = self.runner.invoke(main, ['ask', '-'], input='')
        
        assert result.exit_code == 1
        assert 'No input provided' in result.output