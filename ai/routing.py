"""Unified routing logic for selecting backends and models."""

from typing import Optional, Union, Dict, Any, List
from .models import AIResponse, ImageInput
from .backends import BaseBackend, CloudBackend, HAS_LOCAL_BACKEND

if HAS_LOCAL_BACKEND:
    from .backends import LocalBackend
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
                if not HAS_LOCAL_BACKEND:
                    raise BackendNotAvailableError(
                        "local",
                        "Local backend not available. Install with: pip install ai[local]",
                    )
                self._backends[backend_name] = LocalBackend(config_dict)
            elif backend_name == "cloud":
                self._backends[backend_name] = CloudBackend(config_dict)
            else:
                # Try plugin registry
                backend = plugin_registry.create_backend(backend_name, config_dict)
                if backend:
                    self._backends[backend_name] = backend
                else:
                    raise BackendNotAvailableError(
                        backend_name, "Backend not found in registry"
                    )

        return self._backends[backend_name]

    def resolve_backend(
        self, backend: Optional[Union[str, BaseBackend]] = None
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

        # Handle mock objects (for testing)
        if hasattr(backend, "_mock_name") or str(type(backend)).startswith(
            "<class 'unittest.mock"
        ):
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
                    logger.debug(
                        f"Using configured default backend: {self.config.default_backend}"
                    )
                    return backend
            except Exception as e:
                logger.warning(
                    f"Default backend {self.config.default_backend} failed: {e}"
                )

        # Try cloud first (always available)
        try:
            backend = self.get_backend("cloud")
            if backend.is_available:
                logger.debug("Using cloud backend")
                return backend
        except Exception as e:
            logger.warning(f"Cloud backend failed: {e}")

        # Fallback to local if available
        if HAS_LOCAL_BACKEND:
            try:
                backend = self.get_backend("local")
                if backend.is_available:
                    logger.debug("Using local backend")
                    return backend
            except Exception as e:
                logger.warning(f"Local backend failed: {e}")

        # Try other backends in fallback order
        for backend_name in self.config.fallback_order:
            if backend_name in ["cloud", "local"]:
                continue  # Already tried above
            try:
                backend = self.get_backend(backend_name)
                if backend.is_available:
                    logger.debug(f"Auto-selected backend: {backend_name}")
                    return backend
            except Exception as e:
                logger.debug(f"Backend {backend_name} not available: {e}")

        # No backends available
        error_msg = "No backends available."
        if not HAS_LOCAL_BACKEND:
            error_msg += " For local models: pip install ai[local]"
        raise BackendNotAvailableError("auto", error_msg)

    def resolve_model(
        self, model: Optional[str] = None, backend: Optional[BaseBackend] = None
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
                if backend and hasattr(backend, "default_model"):
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
        **kwargs,
    ) -> tuple[BaseBackend, str]:
        """
        Smart routing that selects backend and model based on preferences and prompt.

        Args:
            prompt: The user prompt - can be a string or list of content (text/images)
            model: Specific model requested
            backend: Specific backend requested
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
                    logger.info(
                        "Images detected, switching to cloud backend with vision model"
                    )
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
            # First check if it's in the registry
            model_info = model_registry.get_model(model)
            if model_info:
                if model_info.provider == "local":
                    selected_backend = self.get_backend("local")
                else:
                    selected_backend = self.get_backend("cloud")
                selected_model = self.resolve_model(model, selected_backend)
                return selected_backend, selected_model
            
            # If not in registry, detect cloud models by naming patterns
            cloud_model_patterns = [
                "openrouter/", "anthropic/", "openai/", "google/", 
                "gpt-", "claude-", "gemini-", "mistral/", "meta/",
                "cohere/", "replicate/", "huggingface/"
            ]
            
            is_cloud_model = any(model.startswith(pattern) for pattern in cloud_model_patterns)
            
            if is_cloud_model:
                logger.debug(f"Detected cloud model pattern: {model}")
                selected_backend = self.get_backend("cloud")
                selected_model = self.resolve_model(model, selected_backend)
                return selected_backend, selected_model




        # Use auto-selection to respect configured default_backend
        selected_backend = self._auto_select_backend()
        
        # Use configured default model
        selected_model = self.resolve_model(model, selected_backend)

        return selected_backend, selected_model


    async def route_with_fallback(
        self,
        prompt: str,
        method: str = "ask",
        *,
        max_retries: Optional[int] = None,
        **kwargs,
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
