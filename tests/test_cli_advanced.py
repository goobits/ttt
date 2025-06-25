"""Advanced tests for CLI module to increase coverage."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typer.testing import CliRunner
from pathlib import Path
import tempfile
import os
import sys

from ai.cli import app
from ai.models import ModelInfo
from ai.backends import LocalBackend, CloudBackend


@pytest.fixture
def runner():
    """Provide CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_config():
    """Mock configuration."""
    with patch('ai.cli.get_config') as mock:
        config_obj = Mock()
        config_obj.timeout = 30
        config_obj.model_aliases = {"fast": "gpt-3.5-turbo"}
        mock.return_value = config_obj
        yield mock


class TestCLIAskCommand:
    """Test the ask command."""
    
    def test_ask_basic(self, runner, mock_config):
        """Test basic ask functionality."""
        with patch('ai.cli.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Test response")
            mock_response.model = "gpt-3.5-turbo"
            mock_response.backend = "local"
            mock_response.time = 0.5
            mock_response.tokens_in = 10
            mock_response.tokens_out = 20
            mock_ask.return_value = mock_response
            
            result = runner.invoke(app, ["What is Python?"])
            
            assert result.exit_code == 0
            assert "Test response" in result.stdout
            mock_ask.assert_called_once_with("What is Python?")
    
    def test_ask_with_model(self, runner, mock_config):
        """Test ask with specific model."""
        with patch('ai.cli.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_ask.return_value = mock_response
            
            result = runner.invoke(app, ["Question", "--model", "gpt-4"])
            
            assert result.exit_code == 0
            call_args = mock_ask.call_args
            assert call_args[1]["model"] == "gpt-4"
    
    def test_ask_with_system(self, runner, mock_config):
        """Test ask with system prompt."""
        with patch('ai.cli.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_ask.return_value = mock_response
            
            result = runner.invoke(app, ["Question", "--system", "You are helpful"])
            
            assert result.exit_code == 0
            call_args = mock_ask.call_args
            assert call_args[1]["system"] == "You are helpful"
    
    def test_ask_with_verbose(self, runner, mock_config):
        """Test ask with verbose output."""
        with patch('ai.cli.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_response.model = "test-model"
            mock_response.backend = "test-backend"
            mock_response.time = 1.5
            mock_response.tokens_in = 15
            mock_response.tokens_out = 25
            mock_response.cost = 0.001
            mock_ask.return_value = mock_response
            
            result = runner.invoke(app, ["Question", "--verbose"])
            
            assert result.exit_code == 0
            assert "Model: test-model" in result.stdout
            assert "Backend: test-backend" in result.stdout
            assert "Time: 1.50s" in result.stdout
            assert "Tokens: 15 → 25" in result.stdout
            assert "Cost: $0.0010" in result.stdout
    
    def test_ask_streaming(self, runner, mock_config):
        """Test ask with streaming."""
        with patch('ai.cli.stream') as mock_stream:
            mock_stream.return_value = iter(["Hello", " ", "world"])
            
            result = runner.invoke(app, ["Question", "--stream"])
            
            assert result.exit_code == 0
            assert "Hello world" in result.stdout
            mock_stream.assert_called_once()
    
    def test_ask_with_temperature(self, runner, mock_config):
        """Test ask with temperature."""
        with patch('ai.cli.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_ask.return_value = mock_response
            
            result = runner.invoke(app, ["Question", "--temperature", "0.5"])
            
            assert result.exit_code == 0
            call_args = mock_ask.call_args
            assert call_args[1]["temperature"] == 0.5
    
    def test_ask_with_max_tokens(self, runner, mock_config):
        """Test ask with max tokens."""
        with patch('ai.cli.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_ask.return_value = mock_response
            
            result = runner.invoke(app, ["Question", "--max-tokens", "100"])
            
            assert result.exit_code == 0
            call_args = mock_ask.call_args
            assert call_args[1]["max_tokens"] == 100
    
    def test_ask_with_backend(self, runner, mock_config):
        """Test ask with specific backend."""
        with patch('ai.cli.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_ask.return_value = mock_response
            
            result = runner.invoke(app, ["Question", "--backend", "cloud"])
            
            assert result.exit_code == 0
            call_args = mock_ask.call_args
            assert call_args[1]["backend"] == "cloud"
    
    def test_ask_with_fast(self, runner, mock_config):
        """Test ask with fast flag."""
        with patch('ai.cli.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_ask.return_value = mock_response
            
            result = runner.invoke(app, ["Question", "--fast"])
            
            assert result.exit_code == 0
            call_args = mock_ask.call_args
            assert call_args[1]["fast"] is True
    
    def test_ask_with_quality(self, runner, mock_config):
        """Test ask with quality flag."""
        with patch('ai.cli.ask') as mock_ask:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Response")
            mock_ask.return_value = mock_response
            
            result = runner.invoke(app, ["Question", "--quality"])
            
            assert result.exit_code == 0
            call_args = mock_ask.call_args
            assert call_args[1]["quality"] is True


class TestCLIConfigCommand:
    """Test config command."""
    
    def test_config_show(self, runner):
        """Test showing configuration."""
        with patch('ai.cli.get_config') as mock_get:
            config = Mock()
            config.default_backend = "auto"
            config.default_model = "gpt-3.5-turbo"
            config.timeout = 30
            config.model_aliases = {"fast": "gpt-3.5-turbo"}
            mock_get.return_value = config
            
            result = runner.invoke(app, ["config"])
            
            assert result.exit_code == 0
            assert "Configuration" in result.stdout
            assert "default_backend" in result.stdout
            assert "auto" in result.stdout
    
    def test_config_path(self, runner):
        """Test showing config path."""
        result = runner.invoke(app, ["config", "--path"])
        
        assert result.exit_code == 0
        assert "Config directory:" in result.stdout
        assert ".config/ai" in result.stdout or "ai" in result.stdout


class TestCLIModelsListCommand:
    """Test models list command."""
    
    def test_models_list_all(self, runner):
        """Test listing all models."""
        with patch('ai.cli.LocalBackend') as mock_local:
            with patch('ai.cli.CloudBackend') as mock_cloud:
                with patch('ai.cli.model_registry') as mock_registry:
                    # Setup model registry mock
                    mock_model1 = Mock()
                    mock_model1.name = "gpt-4"
                    mock_model1.provider = "openai"
                    mock_model1.aliases = ["gpt4"]
                    mock_model1.speed = "fast"
                    mock_model1.quality = "excellent"
                    mock_model1.capabilities = ["text", "code"]
                    mock_model1.context_length = 8192
                    
                    mock_model2 = Mock()
                    mock_model2.name = "claude-3"
                    mock_model2.provider = "anthropic"
                    mock_model2.aliases = ["claude"]
                    mock_model2.speed = "fast"
                    mock_model2.quality = "excellent"
                    mock_model2.capabilities = ["text", "code"]
                    mock_model2.context_length = 100000
                    
                    mock_registry.list_models.return_value = [mock_model1, mock_model2]
                    
                    # Setup mocks
                    local_backend = AsyncMock()
                    local_backend.is_available = True
                    local_backend.list_models = AsyncMock(return_value=["llama2", "mistral"])
                    mock_local.return_value = local_backend
                    
                    cloud_backend = AsyncMock()
                    cloud_backend.is_available = True
                    cloud_backend.list_models = AsyncMock(return_value=[
                        {"name": "gpt-4", "provider": "openai"},
                        {"name": "claude-3", "provider": "anthropic"}
                    ])
                    mock_cloud.return_value = cloud_backend
                    
                    result = runner.invoke(app, ["models", "list"])
                    
                    if result.exit_code != 0:
                        print(f"Error: {result.exception}")
                        print(f"Output: {result.stdout}")
                        if result.exc_info:
                            import traceback
                            traceback.print_exception(*result.exc_info)
                    
                    assert result.exit_code == 0
                    assert "Available Models" in result.stdout
                    assert "Local Models" in result.stdout
                    assert "llama2" in result.stdout
                    assert "Cloud Models" in result.stdout
                    assert "gpt-4" in result.stdout
    
    def test_models_list_local_only(self, runner):
        """Test listing only local models."""
        with patch('ai.cli.LocalBackend') as mock_local:
            local_backend = AsyncMock()
            local_backend.is_available = True
            local_backend.list_models = AsyncMock(return_value=["llama2"])
            mock_local.return_value = local_backend
            
            result = runner.invoke(app, ["models", "list", "--local"])
            
            assert result.exit_code == 0
            assert "Local Models" in result.stdout
            assert "Cloud Models" not in result.stdout
    
    def test_models_list_cloud_only(self, runner):
        """Test listing only cloud models."""
        with patch('ai.cli.CloudBackend') as mock_cloud:
            cloud_backend = AsyncMock()
            cloud_backend.is_available = True
            cloud_backend.list_models = AsyncMock(return_value=[
                {"name": "gpt-4", "provider": "openai"}
            ])
            mock_cloud.return_value = cloud_backend
            
            result = runner.invoke(app, ["models", "list", "--cloud"])
            
            assert result.exit_code == 0
            assert "Cloud Models" in result.stdout
            assert "Local Models" not in result.stdout
    
    def test_models_list_no_backends(self, runner):
        """Test when no backends are available."""
        with patch('ai.cli.LocalBackend') as mock_local:
            with patch('ai.cli.CloudBackend') as mock_cloud:
                mock_local.return_value.is_available = False
                mock_cloud.return_value.is_available = False
                
                result = runner.invoke(app, ["models", "list"])
                
                assert result.exit_code == 0
                assert "No backends available" in result.stdout


class TestBackendStatusCommand:
    """Test backend status command."""
    
    def test_backend_status_basic(self, runner):
        """Test basic backend status."""
        with patch('ai.cli.LocalBackend') as mock_local:
            with patch('ai.cli.CloudBackend') as mock_cloud:
                # Setup local backend
                local_backend = AsyncMock()
                local_backend.is_available = True
                local_backend.status = AsyncMock(return_value={
                    "available": True,
                    "version": "0.1.5",
                    "models": ["llama2"]
                })
                mock_local.return_value = local_backend
                
                # Setup cloud backend
                cloud_backend = AsyncMock()
                cloud_backend.is_available = True
                cloud_backend.status = AsyncMock(return_value={
                    "available": True,
                    "providers": {
                        "openai": {"available": True}
                    }
                })
                mock_cloud.return_value = cloud_backend
                
                result = runner.invoke(app, ["backend", "status"])
                
                assert result.exit_code == 0
                assert "Backend Status" in result.stdout
                assert "Local Backend" in result.stdout
                assert "✓ Available" in result.stdout
                assert "Cloud Backend" in result.stdout


class TestErrorHandling:
    """Test error handling in CLI."""
    
    def test_ask_error_handling(self, runner, mock_config):
        """Test error handling in ask command."""
        with patch('ai.cli.ask') as mock_ask:
            mock_ask.side_effect = Exception("Test error")
            
            result = runner.invoke(app, ["Question"])
            
            assert result.exit_code == 0  # Should handle gracefully
            assert "Error" in result.stdout
            assert "Test error" in result.stdout
    
    def test_stream_error_handling(self, runner, mock_config):
        """Test error handling in stream."""
        with patch('ai.cli.stream') as mock_stream:
            mock_stream.side_effect = Exception("Stream error")
            
            result = runner.invoke(app, ["Question", "--stream"])
            
            assert result.exit_code == 0
            assert "Error" in result.stdout
            assert "Stream error" in result.stdout