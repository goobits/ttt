"""Advanced tests for CLI module to increase coverage."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os
from io import StringIO

# Import CLI functions and exceptions
from ai.cli import main, parse_args
from ai.api import ask, stream
from ai.exceptions import (
    APIKeyError, ModelNotFoundError, RateLimitError,
    BackendNotAvailableError, EmptyResponseError
)


class TestCLIAskCommand:
    """Test the ask functionality."""
    
    @patch('ai.api.ask')
    def test_ask_basic(self, mock_ask):
        """Test basic ask functionality."""
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Test response")
        mock_response.model = "gpt-3.5-turbo"
        mock_response.backend = "cloud"
        mock_response.time = 0.5
        mock_response.tokens_in = 10
        mock_response.tokens_out = 20
        mock_ask.return_value = mock_response
        
        with patch('sys.argv', ['ai', 'What is Python?']):
            with patch('ai.cli.console') as mock_console:
                main()
                
                # Check the ask was called correctly
                mock_ask.assert_called_once()
                call_args = mock_ask.call_args
                assert call_args[0][0] == "What is Python?"
                
                # Check response was printed
                print_calls = [str(call) for call in mock_console.print.call_args_list]
                assert any('Test response' in str(call) for call in print_calls)
    
    @patch('ai.api.ask')
    def test_ask_with_model(self, mock_ask):
        """Test ask with specific model."""
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Response")
        mock_ask.return_value = mock_response
        
        with patch('sys.argv', ['ai', 'Question', '--model', 'gpt-4']):
            with patch('ai.cli.console'):
                main()
                
                call_kwargs = mock_ask.call_args[1]
                assert call_kwargs.get('model') == 'gpt-4'
    
    @patch('ai.api.ask')
    def test_ask_with_system(self, mock_ask):
        """Test ask with system prompt."""
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Response")
        mock_ask.return_value = mock_response
        
        with patch('sys.argv', ['ai', 'Question', '--system', 'You are helpful']):
            with patch('ai.cli.console'):
                main()
                
                call_kwargs = mock_ask.call_args[1]
                assert call_kwargs.get('system') == 'You are helpful'
    
    @patch('ai.api.ask')
    def test_ask_with_verbose(self, mock_ask):
        """Test ask with verbose output."""
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
        
        with patch('sys.argv', ['ai', 'Question', '--verbose']):
            with patch('ai.cli.console') as mock_console:
                main()
                
                # Check that verbose info was shown
                print_calls = [str(call) for call in mock_console.print.call_args_list]
                # Verbose mode should show metadata
                assert any('Response' in str(call) for call in print_calls)
                # CLI uses Panel for verbose metadata
                from rich.panel import Panel
                has_panel = any(
                    len(call[0]) > 0 and isinstance(call[0][0], Panel) 
                    for call in mock_console.print.call_args_list
                )
                assert has_panel or any('Model:' in str(call) for call in print_calls)
    
    @patch('ai.api.stream')
    def test_ask_streaming(self, mock_stream):
        """Test ask with streaming."""
        mock_stream.return_value = iter(["Hello", " ", "world"])
        
        with patch('sys.argv', ['ai', 'Question', '--stream']):
            with patch('ai.cli.console') as mock_console:
                main()
                
                mock_stream.assert_called_once()
                # Check streaming output
                print_calls = mock_console.print.call_args_list
                # Should have printed chunks
                assert len(print_calls) >= 3  # At least the chunks
    
    @patch('ai.api.ask')
    def test_ask_with_temperature(self, mock_ask):
        """Test ask with temperature."""
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Response")
        mock_ask.return_value = mock_response
        
        with patch('sys.argv', ['ai', 'Question', '--temperature', '0.5']):
            with patch('ai.cli.console'):
                main()
                
                call_kwargs = mock_ask.call_args[1]
                assert call_kwargs.get('temperature') == 0.5
    
    @patch('ai.api.ask')
    def test_ask_with_max_tokens(self, mock_ask):
        """Test ask with max tokens."""
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Response")
        mock_ask.return_value = mock_response
        
        with patch('sys.argv', ['ai', 'Question', '--max-tokens', '100']):
            with patch('ai.cli.console'):
                main()
                
                call_kwargs = mock_ask.call_args[1]
                assert call_kwargs.get('max_tokens') == 100
    
    @patch('ai.api.ask')
    def test_ask_with_backend(self, mock_ask):
        """Test ask with specific backend."""
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Response")
        mock_ask.return_value = mock_response
        
        with patch('sys.argv', ['ai', 'Question', '--backend', 'local']):
            with patch('ai.cli.console'):
                main()
                
                call_kwargs = mock_ask.call_args[1]
                assert call_kwargs.get('backend') == 'local'
    
    def test_ask_from_stdin(self):
        """Test reading prompt from stdin."""
        # Test that parse_args correctly parses '-' as prompt
        with patch('sys.argv', ['ai', '-']):
            args = parse_args()
            assert args['command'] == 'query'
            assert args['prompt'] == '-'


class TestCLIErrorHandling:
    """Test error handling in CLI."""
    
    @patch('ai.api.ask')
    def test_api_key_error(self, mock_ask):
        """Test handling of API key errors."""
        mock_ask.side_effect = APIKeyError("openai", "OPENAI_API_KEY")
        
        with patch('sys.argv', ['ai', 'Question']):
            with patch('ai.cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                print_calls = [str(call) for call in mock_console.print.call_args_list]
                assert any('API Key Missing' in str(call) for call in print_calls)
                assert any('OPENAI_API_KEY' in str(call) for call in print_calls)
    
    @patch('ai.api.ask')
    def test_model_not_found_error(self, mock_ask):
        """Test handling of model not found errors."""
        mock_ask.side_effect = ModelNotFoundError("gpt-5", "cloud")
        
        with patch('sys.argv', ['ai', 'Question']):
            with patch('ai.cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                print_calls = [str(call) for call in mock_console.print.call_args_list]
                assert any('Model Not Found' in str(call) for call in print_calls)
                assert any('models-list' in str(call) for call in print_calls)
    
    @patch('ai.api.ask')
    def test_rate_limit_error(self, mock_ask):
        """Test handling of rate limit errors."""
        mock_ask.side_effect = RateLimitError("openai", retry_after=60)
        
        with patch('sys.argv', ['ai', 'Question']):
            with patch('ai.cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                print_calls = [str(call) for call in mock_console.print.call_args_list]
                assert any('Rate Limit Exceeded' in str(call) for call in print_calls)
                assert any('60 seconds' in str(call) for call in print_calls)
    
    @patch('ai.api.ask')
    def test_backend_not_available_error(self, mock_ask):
        """Test handling of backend not available errors."""
        mock_ask.side_effect = BackendNotAvailableError("local", "Ollama not running")
        
        with patch('sys.argv', ['ai', 'Question']):
            with patch('ai.cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                print_calls = [str(call) for call in mock_console.print.call_args_list]
                assert any('Backend Not Available' in str(call) for call in print_calls)
                assert any('backend-status' in str(call) for call in print_calls)
    
    @patch('ai.api.ask')
    def test_empty_response_error(self, mock_ask):
        """Test handling of empty response errors."""
        mock_ask.side_effect = EmptyResponseError("gpt-3.5", "cloud")
        
        with patch('sys.argv', ['ai', 'Question']):
            with patch('ai.cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                print_calls = [str(call) for call in mock_console.print.call_args_list]
                assert any('Empty Response' in str(call) for call in print_calls)
                assert any('Try rephrasing' in str(call) for call in print_calls)
    
    @patch('ai.api.ask')
    def test_generic_error_without_verbose(self, mock_ask):
        """Test handling of generic errors without verbose flag."""
        mock_ask.side_effect = Exception("Some unexpected error")
        
        with patch('sys.argv', ['ai', 'Question']):
            with patch('ai.cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                print_calls = [str(call) for call in mock_console.print.call_args_list]
                assert any('Error' in str(call) for call in print_calls)
                assert any('Some unexpected error' in str(call) for call in print_calls)
                assert any('--verbose' in str(call) for call in print_calls)
    
    @patch('ai.api.ask')
    def test_generic_error_with_verbose(self, mock_ask):
        """Test handling of generic errors with verbose flag."""
        mock_ask.side_effect = Exception("Some unexpected error")
        
        with patch('sys.argv', ['ai', 'Question', '--verbose']):
            with patch('ai.cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                print_calls = [str(call) for call in mock_console.print.call_args_list]
                assert any('Error' in str(call) for call in print_calls)
                assert any('Full traceback' in str(call) for call in print_calls)
    
    @patch('ai.api.stream')
    def test_stream_error_handling(self, mock_stream):
        """Test error handling in stream mode."""
        mock_stream.side_effect = Exception("Stream error")
        
        with patch('sys.argv', ['ai', 'Question', '--stream']):
            with patch('ai.cli.console') as mock_console:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                print_calls = [str(call) for call in mock_console.print.call_args_list]
                assert any('Error' in str(call) for call in print_calls)
                assert any('Stream error' in str(call) for call in print_calls)
    
    def test_keyboard_interrupt(self):
        """Test handling of keyboard interrupt."""
        with patch('sys.argv', ['ai', 'Question']):
            with patch('ai.api.ask') as mock_ask:
                mock_ask.side_effect = KeyboardInterrupt()
                
                with patch('ai.cli.console') as mock_console:
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    assert exc_info.value.code == 1
                    print_calls = [str(call) for call in mock_console.print.call_args_list]
                    assert any('Cancelled by user' in str(call) for call in print_calls)


class TestParseArgs:
    """Test argument parsing."""
    
    def test_parse_empty_args(self):
        """Test parsing with no arguments."""
        with patch('sys.argv', ['ai']):
            args = parse_args()
            assert args['command'] == 'help'
    
    def test_parse_multiple_flags(self):
        """Test parsing with multiple flags."""
        with patch('sys.argv', ['ai', 'Question', '--model', 'gpt-4', '--backend', 'cloud', '--stream', '--verbose']):
            args = parse_args()
            assert args['command'] == 'query'
            assert args['prompt'] == 'Question'
            assert args['model'] == 'gpt-4'
            assert args['backend'] == 'cloud'
            assert args['stream'] is True
            assert args['verbose'] is True
    
    def test_parse_short_flags(self):
        """Test parsing with short flag versions."""
        with patch('sys.argv', ['ai', 'Question', '-m', 'gpt-4', '-s', 'System prompt', '-v']):
            args = parse_args()
            assert args['command'] == 'query'
            assert args['model'] == 'gpt-4'
            assert args['system'] == 'System prompt'
            assert args['verbose'] is True
    
    def test_parse_all_parameters(self):
        """Test parsing with all possible parameters."""
        with patch('sys.argv', [
            'ai', 'Question',
            '--model', 'gpt-4',
            '--system', 'You are helpful',
            '--backend', 'cloud',
            '--temperature', '0.7',
            '--max-tokens', '150',
            '--stream',
            '--verbose'
        ]):
            args = parse_args()
            assert args['command'] == 'query'
            assert args['prompt'] == 'Question'
            assert args['model'] == 'gpt-4'
            assert args['system'] == 'You are helpful'
            assert args['backend'] == 'cloud'
            assert args['temperature'] == 0.7
            assert args['max_tokens'] == 150
            assert args['stream'] is True
            assert args['verbose'] is True