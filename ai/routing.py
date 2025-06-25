"""Unified routing logic for selecting backends and models."""

from typing import Optional, Union, Dict, Any, List
from .models import AIResponse, ImageInput
from .backends import BaseBackend, LocalBackend, CloudBackend
from .config import get_config, model_registry
from .plugins import plugin_registry
from .utils import get_logger
from .exceptions import (
    BackendNotAvailableError,
    ModelNotFoundError,
    InvalidParameterError,
)


logger = get_logger(__name__)


class Router:
    """
    Smart router that selects the best backend and model for each request.
    
    The router handles:
    - Backend selection (local vs cloud vs auto)
    - Model resolution (aliases to actual models)
    - Fallback handling when primary backend fails
    - Smart routing based on query type
    """
    
    def __init__(self):
        self.config = get_config()
        self._backends: Dict[str, BaseBackend] = {}
    
    def get_backend(self, backend_name: str) -> BaseBackend:
        """Get or create a backend instance."""
        if backend_name not in self._backends:
            # Pass the full configuration dict to backends
            config_dict = self.config.model_dump()
            
            # Try built-in backends first
            if backend_name == "local":
                self._backends[backend_name] = LocalBackend(config_dict)
            elif backend_name == "cloud":
                self._backends[backend_name] = CloudBackend(config_dict)
            else:
                # Try plugin registry
                backend = plugin_registry.create_backend(backend_name, config_dict)
                if backend:
                    self._backends[backend_name] = backend
                else:
                    raise BackendNotAvailableError(backend_name, "Backend not found in registry")
        
        return self._backends[backend_name]
    
    def resolve_backend(
        self, 
        backend: Optional[Union[str, BaseBackend]] = None
    ) -> BaseBackend:
        """
        Resolve backend specification to actual backend instance.
        
        Args:
            backend: Backend specification (str, BaseBackend, or None for auto)
            
        Returns:
            BaseBackend instance
        """
        if isinstance(backend, BaseBackend):
            return backend
        
        if isinstance(backend, str):
            return self.get_backend(backend)
        
        # Auto-select backend
        if backend is None:
            return self._auto_select_backend()
        
        raise ValueError(f"Invalid backend specification: {backend}")
    
    def _auto_select_backend(self) -> BaseBackend:
        """
        Automatically select the best available backend.
        
        Returns:
            BaseBackend instance
        """
        # Check default backend preference
        if self.config.default_backend != "auto":
            try:
                backend = self.get_backend(self.config.default_backend)
                if backend.is_available:
                    logger.debug(f"Using configured default backend: {self.config.default_backend}")
                    return backend
            except Exception as e:
                logger.warning(f"Default backend {self.config.default_backend} failed: {e}")
        
        # Try backends in fallback order
        for backend_name in self.config.fallback_order:
            try:
                backend = self.get_backend(backend_name)
                if backend.is_available:
                    logger.debug(f"Auto-selected backend: {backend_name}")
                    return backend
            except Exception as e:
                logger.debug(f"Backend {backend_name} not available: {e}")
        
        # Default to local backend as last resort
        logger.warning("No backends available, falling back to local")
        return self.get_backend("local")
    
    def resolve_model(
        self, 
        model: Optional[str] = None, 
        backend: Optional[BaseBackend] = None
    ) -> str:
        """
        Resolve model specification to actual model name.
        
        Args:
            model: Model name or alias
            backend: Target backend for context
            
        Returns:
            Resolved model name
        """
        if model is None:
            # Use default model from config
            if self.config.default_model:
                model = self.config.default_model
            else:
                # Use backend-specific default
                if backend and hasattr(backend, 'default_model'):
                    return backend.default_model
                return "gpt-3.5-turbo"  # Fallback default
        
        # Try to resolve alias
        resolved = model_registry.resolve_model_name(model)
        logger.debug(f"Resolved model '{model}' to '{resolved}'")
        return resolved
    
    def smart_route(
        self,
        prompt: Union[str, List[Union[str, ImageInput]]],
        *,
        model: Optional[str] = None,
        backend: Optional[Union[str, BaseBackend]] = None,
        prefer_speed: bool = False,
        prefer_quality: bool = False,
        prefer_local: bool = False,
        **kwargs
    ) -> tuple[BaseBackend, str]:
        """
        Smart routing that selects backend and model based on preferences and prompt.
        
        Args:
            prompt: The user prompt - can be a string or list of content (text/images)
            model: Specific model requested
            backend: Specific backend requested
            prefer_speed: Prefer faster models
            prefer_quality: Prefer higher quality models
            prefer_local: Prefer local models for privacy
            **kwargs: Additional parameters
            
        Returns:
            Tuple of (backend, model_name)
        """
        # Check if prompt contains images (multi-modal)
        has_images = False
        if not isinstance(prompt, str):
            has_images = any(isinstance(item, ImageInput) for item in prompt)
            # If images present, must use cloud backend with vision model
            if has_images:
                if backend is None or backend == "local":
                    logger.info("Images detected, switching to cloud backend with vision model")
                    backend = "cloud"
                    if model is None:
                        # Default to a vision-capable model
                        model = "gpt-4-vision-preview"
        
        # If specific backend requested, use it
        if backend is not None:
            selected_backend = self.resolve_backend(backend)
            selected_model = self.resolve_model(model, selected_backend)
            return selected_backend, selected_model
        
        # If specific model requested, determine backend from model
        if model is not None:
            model_info = model_registry.get_model(model)
            if model_info:
                if model_info.provider == "local":
                    selected_backend = self.get_backend("local")
                else:
                    selected_backend = self.get_backend("cloud")
                selected_model = self.resolve_model(model, selected_backend)
                return selected_backend, selected_model
        
        # Smart selection based on preferences
        if prefer_local and not has_images:  # Can't use local with images
            selected_backend = self.get_backend("local")
            selected_model = self._select_model_by_preference(
                "local", prefer_speed, prefer_quality
            )
            return selected_backend, selected_model
        
        # Analyze prompt for hints
        prompt_text = prompt if isinstance(prompt, str) else " ".join(
            item for item in prompt if isinstance(item, str)
        )
        prompt_lower = prompt_text.lower()
        
        # Get routing keywords from config
        config_data = self.config.model_dump()
        routing_config = config_data.get("routing", {})
        
        code_keywords = routing_config.get("code_keywords", [
            "code", "function", "class", "bug", "debug", "programming",
            "python", "javascript", "java", "c++", "rust", "go"
        ])
        
        speed_keywords = routing_config.get("speed_keywords", [
            "what is", "who is", "when", "where", "quick", "simple"
        ])
        
        quality_keywords = routing_config.get("quality_keywords", [
            "analyze", "explain in detail", "comprehensive", "thorough",
            "compare", "contrast", "evaluate"
        ])
        
        # Code-related queries
        if any(keyword in prompt_lower for keyword in code_keywords):
            # Prefer coding models
            if "coding" in model_registry.aliases:
                coding_model = model_registry.aliases["coding"]
                model_info = model_registry.get_model(coding_model)
                if model_info:
                    if model_info.provider == "local":
                        selected_backend = self.get_backend("local")
                    else:
                        selected_backend = self.get_backend("cloud")
                    return selected_backend, coding_model
        
        # Quick questions (prefer speed)
        if any(keyword in prompt_lower for keyword in speed_keywords) or len(prompt) < 50:
            prefer_speed = True
        
        # Complex analysis (prefer quality)
        if any(keyword in prompt_lower for keyword in quality_keywords) or len(prompt) > 200:
            prefer_quality = True
        
        # Select backend and model based on preferences
        if prefer_speed:
            selected_model = self._select_model_by_preference(None, True, False)
        elif prefer_quality:
            selected_model = self._select_model_by_preference(None, False, True)
        else:
            selected_model = self._select_model_by_preference(None, False, False)
        
        # Determine backend from selected model
        model_info = model_registry.get_model(selected_model)
        if model_info and model_info.provider == "local":
            selected_backend = self.get_backend("local")
        else:
            selected_backend = self.get_backend("cloud")
        
        return selected_backend, selected_model
    
    def _select_model_by_preference(
        self,
        provider: Optional[str] = None,
        prefer_speed: bool = False,
        prefer_quality: bool = False
    ) -> str:
        """Select model based on preferences."""
        candidates = []
        
        for name, model_info in model_registry.models.items():
            if provider and model_info.provider != provider:
                continue
            candidates.append((name, model_info))
        
        if not candidates:
            return "gpt-3.5-turbo"  # Fallback
        
        # Score models based on preferences
        scored_models = []
        for name, model_info in candidates:
            score = 0
            
            if prefer_speed:
                if model_info.speed == "fast":
                    score += 3
                elif model_info.speed == "medium":
                    score += 1
            
            if prefer_quality:
                if model_info.quality == "high":
                    score += 3
                elif model_info.quality == "medium":
                    score += 1
            
            # Default preference for balanced models
            if not prefer_speed and not prefer_quality:
                if model_info.quality == "medium" and model_info.speed == "medium":
                    score += 2
            
            scored_models.append((score, name))
        
        # Return highest scoring model
        scored_models.sort(reverse=True)
        selected = scored_models[0][1]
        logger.debug(f"Selected model by preference: {selected}")
        return selected
    
    async def route_with_fallback(
        self,
        prompt: str,
        method: str = "ask",
        *,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """
        Route request with automatic fallback on failure.
        
        Args:
            prompt: The user prompt
            method: Method to call ('ask' or 'astream')
            max_retries: Maximum retries (uses config default if None)
            **kwargs: Parameters for the request
            
        Returns:
            AIResponse from successful backend
        """
        max_retries = max_retries or self.config.max_retries
        
        # Get primary backend and model
        backend, model = self.smart_route(prompt, **kwargs)
        
        # Try primary backend
        try:
            if method == "ask":
                response = await backend.ask(prompt, model=model, **kwargs)
                if not response.failed:
                    return response
        except Exception as e:
            logger.warning(f"Primary backend {backend.name} failed: {e}")
        
        # Try fallback backends if enabled
        if not self.config.enable_fallbacks:
            logger.debug("Fallbacks disabled, returning failed response")
            return AIResponse("", error="Primary backend failed and fallbacks disabled")
        
        # Try other backends
        for backend_name in self.config.fallback_order:
            if backend_name == backend.name:
                continue  # Skip the one we already tried
            
            try:
                fallback_backend = self.get_backend(backend_name)
                if not fallback_backend.is_available:
                    continue
                
                logger.info(f"Trying fallback backend: {backend_name}")
                
                # Resolve model for this backend
                fallback_model = self.resolve_model(model, fallback_backend)
                
                if method == "ask":
                    response = await fallback_backend.ask(
                        prompt, model=fallback_model, **kwargs
                    )
                    if not response.failed:
                        return response
                        
            except Exception as e:
                logger.warning(f"Fallback backend {backend_name} failed: {e}")
        
        # All backends failed
        return AIResponse("", error="All backends failed")


# Global router instance
router = Router()