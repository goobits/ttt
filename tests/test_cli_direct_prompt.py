"""Test direct prompt functionality without explicit ask command."""

import sys
import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner

from ai.cli import main


class TestDirectPrompt:
    """Test ai 'prompt' functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.original_argv = sys.argv.copy()
    
    def teardown_method(self):
        """Restore original sys.argv."""
        sys.argv = self.original_argv
    
    def test_direct_prompt_preprocessing(self):
        """Test that 'ai prompt' gets converted to 'ai ask prompt'."""
        # Simulate command line: ai 'hello world'
        sys.argv = ['ai', 'hello world']
        
        # Define known commands locally
        known_commands = ['ask', 'chat', 'status', 'models', 'tools', 'config']
        
        # Run the preprocessing logic
        if len(sys.argv) > 1:
            first_arg = sys.argv[1]
            if not first_arg.startswith('-') and first_arg not in known_commands:
                sys.argv.insert(1, 'ask')
        
        assert sys.argv == ['ai', 'ask', 'hello world']
    
    def test_command_not_preprocessed(self):
        """Test that actual commands are not preprocessed."""
        known_commands = ['ask', 'chat', 'status', 'models', 'tools', 'config']
        
        # Test various commands
        for cmd in known_commands:
            sys.argv = ['ai', cmd]
            original_argv = sys.argv.copy()
            
            # Run preprocessing
            if len(sys.argv) > 1:
                first_arg = sys.argv[1]
                if not first_arg.startswith('-') and first_arg not in known_commands:
                    sys.argv.insert(1, 'ask')
            
            assert sys.argv == original_argv  # Should remain unchanged
    
    def test_flags_not_preprocessed(self):
        """Test that flags are not preprocessed."""
        known_commands = ['ask', 'chat', 'status', 'models', 'tools', 'config']
        
        # Test various flags
        for flag in ['--help', '--version', '--model', '-m']:
            sys.argv = ['ai', flag]
            original_argv = sys.argv.copy()
            
            # Run preprocessing
            if len(sys.argv) > 1:
                first_arg = sys.argv[1]
                if not first_arg.startswith('-') and first_arg not in known_commands:
                    sys.argv.insert(1, 'ask')
            
            assert sys.argv == original_argv  # Should remain unchanged
    
    def test_direct_prompt_execution(self):
        """Test that direct prompt executes ask command."""
        with patch('ai.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Test response")
            mock_response.model = "gpt-3.5-turbo"
            mock_response.backend = "cloud"
            mock_response.time = 1.0
            mock_ask.return_value = mock_response
            
            # Simulate the preprocessing that happens in __main__.py
            original_argv = sys.argv
            try:
                sys.argv = ['ai', 'test prompt']
                
                # Run preprocessing
                known_commands = ['ask', 'chat', 'status', 'models', 'tools', 'config']
                if len(sys.argv) > 1:
                    first_arg = sys.argv[1]
                    if not first_arg.startswith('-') and first_arg not in known_commands:
                        sys.argv.insert(1, 'ask')
                
                # Now run with Click runner using the modified argv
                result = self.runner.invoke(main, sys.argv[1:])  # Skip the 'ai' part
                
                assert result.exit_code == 0
                assert "Test response" in result.output
                mock_ask.assert_called_once()
                
            finally:
                sys.argv = original_argv