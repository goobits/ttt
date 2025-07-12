"""Tests for new CLI migration features."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai.cli import (
    parse_args, 
    parse_chat_args,
    detect_best_backend,
    check_backend_available,
    is_coding_request,
    apply_coding_optimization
)


class TestArgumentParsing:
    """Test enhanced argument parsing functionality."""
    
    def test_basic_query_parsing(self):
        """Test basic query parsing works like llm."""
        with patch('sys.argv', ['ai', 'What is Python?']):
            args = parse_args()
            assert args['command'] == 'query'
            assert args['prompt'] == 'What is Python?'
    
    def test_flexible_flag_positioning(self):
        """Test flexible flag positioning like llm."""
        test_cases = [
            # Different positions should all work
            ['ai', 'write a function', '--code'],
            ['ai', '--code', 'write a function'],
            ['ai', 'write', '--code', 'a function'],
        ]
        
        for argv in test_cases:
            with patch('sys.argv', argv):
                args = parse_args()
                assert args['command'] == 'query'
                assert args['code'] is True
                # Should reconstruct the prompt correctly
                assert 'write' in args['prompt']
                assert 'function' in args['prompt']
    
    def test_new_flags(self):
        """Test new CLI flags are parsed correctly."""
        with patch('sys.argv', ['ai', 'test', '--offline', '--verbose']):
            args = parse_args()
            assert args['offline'] is True
            assert args['backend'] == 'local'
            assert args['verbose'] is True
        
        with patch('sys.argv', ['ai', 'test', '--online', '--code']):
            args = parse_args()
            assert args['online'] is True
            assert args['backend'] == 'cloud'
            assert args['code'] is True
    
    def test_chat_mode_parsing(self):
        """Test chat mode argument parsing."""
        with patch('sys.argv', ['ai', '--chat', '--model', 'gpt-4', '--verbose']):
            args = parse_args()
            assert args['command'] == 'chat'
            assert args['model'] == 'gpt-4'
            assert args['verbose'] is True
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing flags."""
        with patch('sys.argv', ['ai', 'test', '--backend', 'local', '--model', 'llama2']):
            args = parse_args()
            assert args['backend'] == 'local'
            assert args['model'] == 'llama2'


class TestSmartFeatures:
    """Test smart detection and optimization features."""
    
    def test_coding_request_detection(self):
        """Test automatic coding request detection."""
        coding_prompts = [
            "write a Python function",
            "debug this code",
            "implement an algorithm",
            "fix this JavaScript error",
            "create a SQL query",
        ]
        
        non_coding_prompts = [
            "what is the weather",
            "tell me a story",
            "translate this text",
            "what is quantum physics",
        ]
        
        for prompt in coding_prompts:
            assert is_coding_request(prompt), f"Should detect coding: {prompt}"
        
        for prompt in non_coding_prompts:
            assert not is_coding_request(prompt), f"Should not detect coding: {prompt}"
    
    def test_coding_optimization(self):
        """Test coding optimization application."""
        args = {'code': True, 'backend': 'cloud'}
        kwargs = apply_coding_optimization(args, {})
        
        # Should set coding-optimized system prompt
        assert 'coding assistant' in kwargs.get('system', '').lower()
        
        # Should set lower temperature for focused responses
        assert kwargs.get('temperature') == 0.3
        
        # Should prefer coding-optimized model
        assert 'claude' in kwargs.get('model', '')
    
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'})
    def test_backend_detection_with_api_keys(self):
        """Test backend detection when API keys are available."""
        args = {}
        backend = detect_best_backend(args)
        assert backend == 'cloud'
    
    @patch.dict(os.environ, {}, clear=True)
    def test_backend_detection_no_api_keys(self):
        """Test backend detection when no API keys available."""
        with patch('ai.backends.local.LocalBackend') as mock_local:
            mock_instance = MagicMock()
            mock_instance.is_available = True
            mock_local.return_value = mock_instance
            
            args = {}
            backend = detect_best_backend(args)
            assert backend == 'local'
    
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'})
    def test_backend_availability_check(self):
        """Test backend availability checking."""
        assert check_backend_available('cloud') is True
        
        with patch('ai.backends.local.LocalBackend') as mock_local:
            mock_instance = MagicMock()
            mock_instance.is_available = False
            mock_local.return_value = mock_instance
            
            assert check_backend_available('local') is False


class TestCLIHelpers:
    """Test CLI helper functions."""
    
    def test_system_commands(self):
        """Test system command parsing."""
        with patch('sys.argv', ['ai', 'backend-status']):
            args = parse_args()
            assert args['command'] == 'backend-status'
        
        with patch('sys.argv', ['ai', 'models-list']):
            args = parse_args()
            assert args['command'] == 'models-list'
        
        with patch('sys.argv', ['ai', '--help']):
            args = parse_args()
            assert args['command'] == 'help'
    
    def test_stdin_support(self):
        """Test stdin input support."""
        with patch('sys.argv', ['ai', '-']):
            args = parse_args()
            assert args['prompt'] == '-'


class TestIntegration:
    """Integration tests for CLI functionality."""
    
    @patch('ai.cli.load_dotenv')
    @patch('ai.api.ask')
    def test_basic_query_flow(self, mock_ask, mock_dotenv):
        """Test basic query execution flow."""
        mock_response = MagicMock()
        mock_response.model = 'test-model'
        mock_response.time = 1.0
        mock_ask.return_value = mock_response
        
        # This would normally be tested with subprocess, 
        # but we're testing the logic flow
        with patch('sys.argv', ['ai', 'test question']):
            args = parse_args()
            assert args['command'] == 'query'
            assert args['prompt'] == 'test question'
    
    def test_help_display(self):
        """Test help display works."""
        with patch('sys.argv', ['ai', '--help']):
            args = parse_args()
            assert args['command'] == 'help'


if __name__ == '__main__':
    pytest.main([__file__])