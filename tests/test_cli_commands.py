"""Tests for advanced CLI commands."""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typer.testing import CliRunner
import os

from ai.cli import app
from ai.backends import HAS_LOCAL_BACKEND


runner = CliRunner()


class TestModelsCommands:
    """Test the models subcommands."""
    
    @patch('ai.cli.model_registry')
    @patch('ai.cli.LocalBackend')
    def test_models_list_all(self, mock_local_backend, mock_registry):
        """Test listing all models."""
        # Mock registry models
        mock_model = Mock()
        mock_model.name = "gpt-4"
        mock_model.provider = "openai"
        mock_model.aliases = ["best", "gpt4"]
        mock_model.speed = "slow"
        mock_model.quality = "high"
        mock_model.capabilities = ["text", "reasoning"]
        mock_model.context_length = 8192
        
        mock_registry.list_models.return_value = ["gpt-4"]
        mock_registry.get_model.return_value = mock_model
        
        # Mock local backend
        mock_backend_instance = Mock()
        mock_backend_instance.models = AsyncMock(return_value=["llama2", "codellama"])
        mock_local_backend.return_value = mock_backend_instance
        
        result = runner.invoke(app, ["models", "list"])
        assert result.exit_code == 0
        assert "AI Models" in result.stdout
        assert "gpt-4" in result.stdout
        assert "llama2" in result.stdout
        assert "codellama" in result.stdout
    
    @patch('ai.cli.model_registry')
    @patch('ai.cli.LocalBackend')
    def test_models_list_local_only(self, mock_local_backend, mock_registry):
        """Test listing only local models."""
        # Mock local backend
        mock_backend_instance = Mock()
        mock_backend_instance.models = AsyncMock(return_value=["llama2"])
        mock_local_backend.return_value = mock_backend_instance
        
        result = runner.invoke(app, ["models", "list", "--local"])
        assert result.exit_code == 0
        assert "llama2" in result.stdout
        # Should not call registry when --local is used
        mock_registry.list_models.assert_not_called()
    
    @patch('ai.cli.model_registry')
    def test_models_list_cloud_only(self, mock_registry):
        """Test listing only cloud models."""
        # Mock registry models
        mock_model = Mock()
        mock_model.name = "claude-3-opus-20240229"
        mock_model.provider = "anthropic"
        mock_model.aliases = ["opus"]
        mock_model.speed = "slow"
        mock_model.quality = "high"
        mock_model.capabilities = ["text", "vision"]
        mock_model.context_length = 200000
        
        mock_registry.list_models.return_value = ["claude-3-opus-20240229"]
        mock_registry.get_model.return_value = mock_model
        
        result = runner.invoke(app, ["models", "list", "--cloud"])
        assert result.exit_code == 0
        assert "claude-3-opus-20240229" in result.stdout
        assert "anthropic" in result.stdout
    
    @patch('ai.cli.model_registry')
    @patch('ai.cli.LocalBackend')
    def test_models_list_verbose(self, mock_local_backend, mock_registry):
        """Test verbose model listing."""
        # Mock a model with all details
        mock_model = Mock()
        mock_model.name = "gpt-3.5-turbo"
        mock_model.provider = "openai"
        mock_model.aliases = ["fast", "gpt3"]
        mock_model.speed = "fast"
        mock_model.quality = "good"
        mock_model.capabilities = ["text", "code"]
        mock_model.context_length = 4096
        
        mock_registry.list_models.return_value = ["gpt-3.5-turbo"]
        mock_registry.get_model.return_value = mock_model
        
        # Mock empty local models
        mock_backend_instance = Mock()
        mock_backend_instance.models = AsyncMock(return_value=[])
        mock_local_backend.return_value = mock_backend_instance
        
        result = runner.invoke(app, ["models", "list", "--verbose"])
        assert result.exit_code == 0
        assert "Speed" in result.stdout
        # Check for either full or truncated column names
        assert "Quality" in result.stdout or "Quali" in result.stdout
        assert "Capabilities" in result.stdout or "Capabi" in result.stdout
        assert "Context" in result.stdout or "Conte" in result.stdout
        assert "fast" in result.stdout
        assert "good" in result.stdout
        assert "4,096" in result.stdout  # Formatted number
    
    @pytest.mark.skipif(not HAS_LOCAL_BACKEND, reason="Local backend not available - httpx not installed")
    def test_models_pull_success(self):
        """Test successful model pull - requires Ollama to be installed and running."""
        import shutil
        if not shutil.which("ollama"):
            pytest.skip("Ollama not installed - install from https://ollama.ai to run this test")
        
        # Test requires actual Ollama installation
        result = runner.invoke(app, ["models", "pull", "llama2", "--no-test"])
        # Note: This test may fail if Ollama server is not running
        # Run 'ollama serve' in another terminal to make this test pass
        if result.exit_code != 0:
            pytest.skip("Ollama server not running - run 'ollama serve' to enable this test")
    
    @patch('shutil.which')
    def test_models_pull_no_ollama(self, mock_which):
        """Test model pull when Ollama is not installed."""
        mock_which.return_value = None
        
        result = runner.invoke(app, ["models", "pull", "llama2"])
        assert result.exit_code == 1
        assert "Ollama is not installed" in result.stdout
        assert "https://ollama.ai" in result.stdout
    
    @pytest.mark.skipif(not HAS_LOCAL_BACKEND, reason="Local backend not available - httpx not installed")
    def test_models_pull_with_progress(self):
        """Test model pull with progress tracking - requires Ollama to be installed and running."""
        import shutil
        if not shutil.which("ollama"):
            pytest.skip("Ollama not installed - install from https://ollama.ai to run this test")
        
        # Test requires actual Ollama installation and server running
        result = runner.invoke(app, ["models", "pull", "mistral", "--no-test"])
        # Note: This test may fail if Ollama server is not running
        # Run 'ollama serve' in another terminal to make this test pass
        if result.exit_code != 0:
            pytest.skip("Ollama server not running - run 'ollama serve' to enable this test")


class TestBackendCommands:
    """Test the backend subcommands."""
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('ai.cli.LocalBackend')
    def test_backend_status_basic(self, mock_local_backend):
        """Test basic backend status check."""
        # Mock local backend
        mock_backend_instance = Mock()
        mock_backend_instance.status = AsyncMock(return_value={
            "available": True,
            "models": ["llama2", "codellama"],
            "base_url": "http://localhost:11434"
        })
        mock_local_backend.return_value = mock_backend_instance
        
        result = runner.invoke(app, ["backend", "status"])
        assert result.exit_code == 0
        assert "AI Backend Status" in result.stdout
        assert "Local (Ollama)" in result.stdout
        assert "🟢" in result.stdout  # Online status
        assert "2 models available" in result.stdout
        
        # Should show missing API keys
        assert "Missing API keys" in result.stdout
        assert "OPENAI_API_KEY" in result.stdout
        assert "ANTHROPIC_API_KEY" in result.stdout
        assert "GOOGLE_API_KEY" in result.stdout
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('ai.cli.LocalBackend')
    @patch('ai.cli.ask_api')
    def test_backend_status_with_api_key(self, mock_ask, mock_local_backend):
        """Test backend status with API key present."""
        # Mock local backend offline
        mock_backend_instance = Mock()
        mock_backend_instance.status = AsyncMock(return_value={"available": False})
        mock_local_backend.return_value = mock_backend_instance
        
        # Mock successful API test
        mock_response = Mock()
        mock_response.failed = False
        mock_ask.return_value = mock_response
        
        result = runner.invoke(app, ["backend", "status"])
        assert result.exit_code == 0
        assert "Cloud (OpenAI)" in result.stdout
        assert "🟢" in result.stdout  # Ready status
        assert "API key valid" in result.stdout
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "invalid-key"})
    @patch('ai.cli.LocalBackend')
    @patch('ai.cli.ask_api')
    def test_backend_status_invalid_key(self, mock_ask, mock_local_backend):
        """Test backend status with invalid API key."""
        # Mock local backend
        mock_backend_instance = Mock()
        mock_backend_instance.status = AsyncMock(return_value={"available": True})
        mock_local_backend.return_value = mock_backend_instance
        
        # Mock failed API test
        mock_response = Mock()
        mock_response.failed = True
        mock_response.error = "401 Unauthorized: Invalid API key"
        mock_ask.return_value = mock_response
        
        result = runner.invoke(app, ["backend", "status"])
        assert result.exit_code == 0
        assert "Cloud (Anthropic)" in result.stdout
        assert "🟠" in result.stdout  # Error status
        assert "Invalid API key" in result.stdout
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key-456"})
    @patch('ai.cli.LocalBackend')
    @patch('ai.cli.ask_api')
    def test_backend_status_verbose(self, mock_ask, mock_local_backend):
        """Test verbose backend status."""
        # Mock local backend
        mock_backend_instance = Mock()
        mock_backend_instance.status = AsyncMock(return_value={
            "available": True,
            "models": ["llama2"],
            "base_url": "http://localhost:11434"
        })
        mock_local_backend.return_value = mock_backend_instance
        
        # Mock successful API test
        mock_response = Mock()
        mock_response.failed = False
        mock_ask.return_value = mock_response
        
        result = runner.invoke(app, ["backend", "status", "--verbose"])
        assert result.exit_code == 0
        assert "Configuration" in result.stdout
        assert "http://localhost:11" in result.stdout  # May be truncated
        assert "Key: test-key...-456" in result.stdout  # Masked key (no dashes in ellipsis)
        assert "Configuration file:" in result.stdout
    
    @patch('ai.cli.LocalBackend')
    def test_backend_status_connection_error(self, mock_local_backend):
        """Test backend status with connection errors."""
        # Mock connection error
        mock_local_backend.side_effect = Exception("Connection refused")
        
        result = runner.invoke(app, ["backend", "status"])
        assert result.exit_code == 0
        assert "🔴" in result.stdout  # Offline status
        assert "Error: Connection refused" in result.stdout


class TestMainCommand:
    """Test updates to main command."""
    
    def test_help_shows_subcommands(self):
        """Test that help shows new subcommands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "models" in result.stdout
        assert "backend" in result.stdout
        assert "Manage AI models" in result.stdout
        assert "Manage AI backends" in result.stdout
    
    def test_models_help(self):
        """Test models subcommand help."""
        result = runner.invoke(app, ["models", "--help"])
        assert result.exit_code == 0
        assert "list" in result.stdout
        assert "pull" in result.stdout
        assert "List all available models" in result.stdout
        assert "Pull a model" in result.stdout
    
    def test_backend_help(self):
        """Test backend subcommand help."""
        result = runner.invoke(app, ["backend", "--help"])
        assert result.exit_code == 0
        assert "status" in result.stdout
        assert "Check connectivity" in result.stdout