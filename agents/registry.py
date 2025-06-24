"""
Model registry and configuration for Agents.py

Manages available models and their capabilities.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from .errors import AgentModelNotFoundError


@dataclass
class ModelInfo:
    """Information about an available model."""
    name: str  # User-facing name
    provider: str  # Provider (openai, anthropic, google)
    provider_name: str  # Provider-specific model name for API calls
    aliases: List[str] = field(default_factory=list)
    capabilities: Dict[str, Any] = field(default_factory=dict)
    speed: str = "medium"  # fast, medium, slow
    quality: str = "medium"  # low, medium, high
    cost: str = "medium"  # low, medium, high
    
    def supports(self, capability: str) -> bool:
        """Check if model supports a capability."""
        return self.capabilities.get(capability, False)


class ModelConfiguration:
    """Manages model registry and configuration."""
    
    def __init__(self):
        """Initialize with default models."""
        self._models: Dict[str, ModelInfo] = {}
        self._default_model: Optional[str] = None
        self._load_default_models()
    
    def _load_default_models(self):
        """Load the default set of models."""
        # OpenAI models
        self.add_model(ModelInfo(
            name="gpt-4o",
            provider="openai",
            provider_name="gpt-4o",
            aliases=["gpt4", "gpt-4"],
            speed="medium",
            quality="high",
            cost="high",
            capabilities={"vision": True, "json": True, "tools": True}
        ))
        
        self.add_model(ModelInfo(
            name="gpt-4o-mini",
            provider="openai",
            provider_name="gpt-4o-mini",
            aliases=["gpt4-mini", "gpt-4-mini", "mini"],
            speed="fast",
            quality="medium",
            cost="low",
            capabilities={"vision": True, "json": True, "tools": True}
        ))
        
        # Anthropic models
        self.add_model(ModelInfo(
            name="claude-3-5-sonnet",
            provider="anthropic",
            provider_name="claude-3-5-sonnet-latest",
            aliases=["claude", "claude-3", "sonnet"],
            speed="medium",
            quality="high",
            cost="medium",
            capabilities={"vision": True, "json": True}
        ))
        
        self.add_model(ModelInfo(
            name="claude-3-5-haiku",
            provider="anthropic",
            provider_name="claude-3-5-haiku-latest",
            aliases=["haiku", "claude-haiku"],
            speed="fast",
            quality="medium",
            cost="low",
            capabilities={"vision": True, "json": True}
        ))
        
        # Google models
        self.add_model(ModelInfo(
            name="gemini-2.0-flash-exp",
            provider="google",
            provider_name="gemini/gemini-2.0-flash-exp",
            aliases=["gemini", "gemini-flash", "flash"],
            speed="fast",
            quality="high",
            cost="low",
            capabilities={"vision": True, "json": True, "tools": True}
        ))
        
        self.add_model(ModelInfo(
            name="gemini-1.5-pro",
            provider="google",
            provider_name="gemini/gemini-1.5-pro-latest",
            aliases=["gemini-pro"],
            speed="medium",
            quality="high",
            cost="medium",
            capabilities={"vision": True, "json": True, "tools": True}
        ))
        
        # OpenRouter models (when OPENROUTER_API_KEY is set)
        import os
        if os.getenv("OPENROUTER_API_KEY"):
            self.add_model(ModelInfo(
                name="openrouter/gemini-flash-1.5",
                provider="openrouter",
                provider_name="openrouter/google/gemini-flash-1.5",
                aliases=["or-gemini-flash"],
                speed="fast",
                quality="high",
                cost="low",
                capabilities={"vision": True, "json": True}
            ))
            
            self.add_model(ModelInfo(
                name="openrouter/gpt-4",
                provider="openrouter",
                provider_name="openrouter/openai/gpt-4",
                aliases=["or-gpt4"],
                speed="medium",
                quality="high",
                cost="high",
                capabilities={"vision": False, "json": True, "tools": True}
            ))
            
            self.add_model(ModelInfo(
                name="openrouter/claude-3-sonnet",
                provider="openrouter",
                provider_name="openrouter/anthropic/claude-3-sonnet",
                aliases=["or-claude"],
                speed="medium",
                quality="high",
                cost="medium",
                capabilities={"vision": True, "json": True}
            ))
        
        # Set default
        self._default_model = "claude-3-5-sonnet"
    
    def add_model(self, model: ModelInfo):
        """Add a model to the registry."""
        self._models[model.name] = model
        
        # Also register aliases
        for alias in model.aliases:
            self._models[alias] = model
    
    def get_model(self, name: str) -> ModelInfo:
        """
        Get model info by name or alias.
        
        Raises:
            AgentModelNotFoundError: If model not found
        """
        if name in self._models:
            return self._models[name]
        
        raise AgentModelNotFoundError(
            f"Model '{name}' not found. Available models: {self.list_models()}"
        )
    
    def get_default_model(self) -> ModelInfo:
        """Get the default model."""
        if self._default_model:
            return self.get_model(self._default_model)
        
        # Fallback to first available model
        if self._models:
            return next(iter(self._models.values()))
        
        raise AgentModelNotFoundError("No models configured")
    
    def set_default_model(self, name: str):
        """Set the default model."""
        # Verify it exists
        self.get_model(name)
        self._default_model = name
    
    def list_models(self) -> List[str]:
        """List all available model names (excluding aliases)."""
        seen = set()
        models = []
        
        for name, info in self._models.items():
            if info.name not in seen:
                seen.add(info.name)
                models.append(info.name)
        
        return sorted(models)
    
    def find_models_by_capability(self, capability: str) -> List[ModelInfo]:
        """Find all models that support a specific capability."""
        seen = set()
        models = []
        
        for info in self._models.values():
            if info.name not in seen and info.supports(capability):
                seen.add(info.name)
                models.append(info)
        
        return models
    
    def find_fastest_model(self) -> ModelInfo:
        """Find the fastest available model."""
        fast_models = [m for m in self._models.values() if m.speed == "fast"]
        if fast_models:
            return fast_models[0]
        return self.get_default_model()
    
    def find_best_quality_model(self) -> ModelInfo:
        """Find the highest quality model."""
        high_quality = [m for m in self._models.values() if m.quality == "high"]
        if high_quality:
            # Prefer models that are also not slow
            for model in high_quality:
                if model.speed != "slow":
                    return model
            return high_quality[0]
        return self.get_default_model()


# Create a default global configuration for backward compatibility
_default_config = ModelConfiguration()


def get_default_configuration() -> ModelConfiguration:
    """Get the default global configuration."""
    return _default_config