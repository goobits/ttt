"""Tests for the data models."""

import pytest
from datetime import datetime
from ai.models import AIResponse, ModelInfo, ConfigModel


class TestAIResponse:
    """Test AIResponse class."""
    
    def test_basic_string_behavior(self):
        """Test that AIResponse behaves like a string."""
        response = AIResponse("Hello, world!")
        
        # Should behave like a string
        assert str(response) == "Hello, world!"
        assert len(response) == 13
        assert response.upper() == "HELLO, WORLD!"
        assert "world" in response
    
    def test_metadata_storage(self):
        """Test metadata is stored correctly."""
        response = AIResponse(
            "Test response",
            model="gpt-3.5-turbo",
            backend="cloud",
            tokens_in=10,
            tokens_out=20,
            time_taken=1.5,
            cost=0.01
        )
        
        assert response.model == "gpt-3.5-turbo"
        assert response.backend == "cloud"
        assert response.tokens_in == 10
        assert response.tokens_out == 20
        assert response.time_taken == 1.5
        assert response.time == 1.5  # Alias
        assert response.cost == 0.01
        assert response.succeeded
        assert not response.failed
    
    def test_error_handling(self):
        """Test error state handling."""
        response = AIResponse(
            "",
            model="test-model",
            error="Test error"
        )
        
        assert response.error == "Test error"
        assert response.failed
        assert not response.succeeded
    
    def test_timestamp_default(self):
        """Test that timestamp is set by default."""
        response = AIResponse("test")
        assert isinstance(response.timestamp, datetime)
    
    def test_repr(self):
        """Test string representation."""
        response = AIResponse(
            "A long response that should be truncated for display",
            model="test-model",
            backend="test",
            time_taken=0.5
        )
        
        repr_str = repr(response)
        assert "AIResponse" in repr_str
        assert "test-model" in repr_str
        assert "test" in repr_str
        assert "0.50s" in repr_str


class TestModelInfo:
    """Test ModelInfo dataclass."""
    
    def test_basic_creation(self):
        """Test basic model creation."""
        model = ModelInfo(
            name="test-model",
            provider="test",
            provider_name="test-provider-model"
        )
        
        assert model.name == "test-model"
        assert model.provider == "test"
        assert model.provider_name == "test-provider-model"
        assert model.aliases == []
        assert model.capabilities == []
    
    def test_with_optional_fields(self):
        """Test model with all fields."""
        model = ModelInfo(
            name="gpt-4",
            provider="openai",
            provider_name="gpt-4",
            aliases=["best", "quality"],
            speed="slow",
            quality="high",
            capabilities=["text", "reasoning"],
            context_length=8192,
            cost_per_token=0.00003
        )
        
        assert model.aliases == ["best", "quality"]
        assert model.speed == "slow"
        assert model.quality == "high"
        assert model.capabilities == ["text", "reasoning"]
        assert model.context_length == 8192
        assert model.cost_per_token == 0.00003


class TestConfigModel:
    """Test ConfigModel configuration."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ConfigModel()
        
        assert config.ollama_base_url == "http://localhost:11434"
        assert config.default_backend == "cloud"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.enable_fallbacks is True
        assert config.fallback_order == ["cloud", "local"]
    
    def test_model_aliases(self):
        """Test default model aliases."""
        config = ConfigModel()
        
        assert "fast" in config.model_aliases
        assert "best" in config.model_aliases
        assert "cheap" in config.model_aliases
        assert "coding" in config.model_aliases
        assert "local" in config.model_aliases
    
    def test_custom_values(self):
        """Test setting custom values."""
        config = ConfigModel(
            ollama_base_url="http://custom:8080",
            default_backend="local",
            timeout=60
        )
        
        assert config.ollama_base_url == "http://custom:8080"
        assert config.default_backend == "local"
        assert config.timeout == 60