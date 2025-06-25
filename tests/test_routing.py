"""Tests for the routing system."""

import pytest
from unittest.mock import Mock, patch
from ai.routing import Router
from ai.backends import BaseBackend
from ai.models import AIResponse, ModelInfo
from ai.config import model_registry
from ai.plugins import plugin_registry
from ai.exceptions import BackendNotAvailableError


class MockBackend(BaseBackend):
    """Mock backend for testing."""
    
    def __init__(self, config=None):
        super().__init__(config)
        self._name = config.get("name", "mock") if config else "mock"
        self._available = True
    
    @property
    def name(self):
        return self._name
    
    @property
    def is_available(self):
        return self._available
    
    async def ask(self, prompt, **kwargs):
        return AIResponse(f"Mock response", model=kwargs.get("model", "mock"), backend=self.name)
    
    async def astream(self, prompt, **kwargs):
        yield "Mock response"
    
    async def models(self):
        return ["mock-model"]
    
    async def status(self):
        return {"backend": self.name, "available": True}


class TestRouter:
    """Test the Router class."""
    
    def test_router_initialization(self):
        """Test router initialization."""
        router = Router()
        assert router.config is not None
        assert router._backends == {}
    
    def test_get_backend_local(self):
        """Test getting local backend."""
        router = Router()
        backend = router.get_backend("local")
        
        assert backend is not None
        assert backend.name == "local"
        assert backend in router._backends.values()
    
    def test_get_backend_cloud(self):
        """Test getting cloud backend."""
        router = Router()
        backend = router.get_backend("cloud")
        
        assert backend is not None
        assert backend.name == "cloud"
        assert backend in router._backends.values()
    
    def test_get_backend_from_plugin(self):
        """Test getting backend from plugin registry."""
        # Register a test backend
        plugin_registry.register_backend("plugin-test", MockBackend)
        
        router = Router()
        backend = router.get_backend("plugin-test")
        
        assert backend is not None
        assert backend.name == "mock"  # MockBackend returns "mock" as name
    
    def test_get_backend_invalid(self):
        """Test getting invalid backend raises error."""
        router = Router()
        
        with pytest.raises(BackendNotAvailableError, match="Backend not found in registry"):
            router.get_backend("non-existent")
    
    def test_resolve_backend_instance(self):
        """Test resolving a backend instance."""
        router = Router()
        mock_backend = MockBackend()
        
        resolved = router.resolve_backend(mock_backend)
        assert resolved is mock_backend
    
    def test_resolve_backend_string(self):
        """Test resolving a backend by name."""
        router = Router()
        resolved = router.resolve_backend("local")
        
        assert resolved is not None
        assert resolved.name == "local"
    
    def test_resolve_backend_auto(self):
        """Test auto backend selection."""
        router = Router()
        
        with patch.object(router, "_auto_select_backend") as mock_auto:
            mock_auto.return_value = MockBackend()
            
            resolved = router.resolve_backend(None)
            mock_auto.assert_called_once()
    
    def test_resolve_model_with_alias(self):
        """Test model resolution with aliases."""
        router = Router()
        
        # The default registry should have "fast" alias
        resolved = router.resolve_model("fast")
        assert resolved == "gpt-3.5-turbo"  # Default fast alias
    
    def test_resolve_model_without_alias(self):
        """Test model resolution without alias."""
        router = Router()
        
        resolved = router.resolve_model("some-model")
        assert resolved == "some-model"  # Returns as-is
    
    def test_resolve_model_none(self):
        """Test model resolution with None."""
        router = Router()
        mock_backend = MockBackend()
        mock_backend.default_model = "backend-default"
        
        # With backend default
        resolved = router.resolve_model(None, backend=mock_backend)
        assert resolved == "backend-default"
        
        # Without backend, uses fallback
        resolved = router.resolve_model(None)
        assert resolved == "gpt-3.5-turbo"  # Fallback default


class TestSmartRouting:
    """Test smart routing functionality."""
    
    def test_smart_route_explicit_backend(self):
        """Test routing with explicit backend."""
        router = Router()
        
        backend, model = router.smart_route(
            "Test prompt",
            backend="local",
            model="llama2"
        )
        
        assert backend.name == "local"
        assert model == "llama2"
    
    def test_smart_route_explicit_model(self):
        """Test routing with explicit model determines backend."""
        router = Router()
        
        # Add a local model to registry
        model_registry.add_model(ModelInfo(
            name="test-local-model",
            provider="local",
            provider_name="test"
        ))
        
        backend, model = router.smart_route(
            "Test prompt",
            model="test-local-model"
        )
        
        assert backend.name == "local"
        assert model == "test-local-model"
    
    def test_smart_route_prefer_local(self):
        """Test routing with prefer_local flag."""
        router = Router()
        
        backend, model = router.smart_route(
            "Test prompt",
            prefer_local=True
        )
        
        assert backend.name == "local"
    
    def test_smart_route_code_detection(self):
        """Test routing detects code-related queries."""
        router = Router()
        
        # Ensure coding alias exists
        if "coding" not in model_registry.aliases:
            model_registry.add_model(ModelInfo(
                name="claude-3-sonnet",
                provider="cloud",
                provider_name="claude-3-sonnet-20240229",
                aliases=["coding"]
            ))
        
        backend, model = router.smart_route(
            "Write a Python function to sort a list"
        )
        
        # Should select the coding model
        assert model == "claude-3-sonnet"
    
    def test_smart_route_speed_preference(self):
        """Test routing with speed preference."""
        router = Router()
        
        backend, model = router.smart_route(
            "What is 2+2?",  # Short question implies speed preference
            prefer_speed=True
        )
        
        # Should select a fast model
        model_info = model_registry.get_model(model)
        if model_info:
            assert model_info.speed == "fast"
    
    def test_smart_route_quality_preference(self):
        """Test routing with quality preference."""
        router = Router()
        
        backend, model = router.smart_route(
            "Provide a comprehensive analysis of quantum computing",
            prefer_quality=True
        )
        
        # Should select a high-quality model
        model_info = model_registry.get_model(model)
        if model_info:
            assert model_info.quality == "high"
    
    def test_smart_route_custom_keywords(self):
        """Test routing with custom keywords from config."""
        router = Router()
        
        # Mock config with custom keywords
        with patch.object(router, 'config') as mock_config:
            mock_config.model_dump.return_value = {
                "routing": {
                    "code_keywords": ["algorithm", "implement"],
                    "speed_keywords": ["quick", "brief"],
                    "quality_keywords": ["detailed", "thorough"]
                }
            }
            
            # Test code keyword detection
            backend, model = router.smart_route("Implement an algorithm")
            # Should trigger code routing logic
            
            # Test speed keyword detection  
            backend, model = router.smart_route("Give me a brief answer", fast=True)
            model_info = model_registry.get_model(model)
            if model_info:
                assert model_info.speed == "fast"


class TestRouterFallback:
    """Test router fallback functionality."""
    
    @pytest.mark.asyncio
    async def test_route_with_fallback_success(self):
        """Test successful routing without fallback."""
        router = Router()
        
        # Mock successful response
        mock_backend = MockBackend()
        
        with patch.object(router, "smart_route") as mock_route:
            mock_route.return_value = (mock_backend, "mock-model")
            
            response = await router.route_with_fallback("Test prompt")
            
            assert response.backend == "mock"
            assert not response.failed
    
    @pytest.mark.asyncio
    async def test_route_with_fallback_retry(self):
        """Test routing with fallback on failure."""
        router = Router()
        
        # Create failing and successful backends
        failing_backend = MockBackend({"name": "failing"})
        failing_backend._available = False
        
        success_backend = MockBackend({"name": "success"})
        
        # Mock the get_backend method
        def mock_get_backend(name):
            if name == "cloud":
                return failing_backend
            elif name == "local":
                return success_backend
            raise ValueError(f"Unknown backend: {name}")
        
        with patch.object(router, "get_backend", side_effect=mock_get_backend):
            with patch.object(router, "smart_route") as mock_route:
                mock_route.return_value = (failing_backend, "model")
                
                # Mock ask to fail on first backend
                async def mock_ask(prompt, **kwargs):
                    if kwargs.get("model") == "model":
                        return AIResponse("", error="Failed", backend="failing")
                    return AIResponse("Success", backend="success")
                
                failing_backend.ask = mock_ask
                success_backend.ask = mock_ask
                
                response = await router.route_with_fallback("Test prompt")
                
                # Should have tried fallback
                assert response.backend == "success"