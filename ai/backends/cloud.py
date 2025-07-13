"""Cloud backend implementation using LiteLLM for multiple providers."""

import time
import json
from typing import AsyncIterator, Dict, Any, Optional, List, Union
import os
from ..models import AIResponse, ImageInput
from ..utils import get_logger
from .base import BaseBackend
from ..config import model_registry  # Import the central registry
from ..exceptions import (
    BackendNotAvailableError,
    BackendConnectionError,
    BackendTimeoutError,
    ModelNotFoundError,
    APIKeyError,
    EmptyResponseError,
    RateLimitError,
    QuotaExceededError,
)


logger = get_logger(__name__)


class CloudBackend(BaseBackend):
    """
    Cloud backend that uses LiteLLM to access multiple AI providers.

    Supports OpenAI, Anthropic, Google, and many other providers through
    a unified interface.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the cloud backend.

        Args:
            config: Configuration dictionary containing API keys and settings
        """
        super().__init__(config)

        # Import LiteLLM here to avoid import errors if not installed
        try:
            import litellm

            self.litellm = litellm
        except ImportError:
            raise BackendNotAvailableError(
                "cloud",
                "LiteLLM is required for cloud backend. Install with: pip install litellm",
            )

        # Default models for different providers
        self.default_models = {
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-sonnet-20240229",
            "google": "gemini-pro",
            "openrouter": "openrouter/google/gemini-flash-1.5",
        }

        # Get default model from backend_config (handles merging)
        self.default_model = self.backend_config.get("default_model", "gpt-3.5-turbo")

        # Get provider order preference
        self.provider_order = self.backend_config.get(
            "provider_order", ["openai", "anthropic", "google"]
        )

        # Configure API keys from environment
        self._configure_api_keys()

    def _configure_api_keys(self) -> None:
        """Configure API keys from environment variables."""
        # OpenAI
        if openai_key := (
            self.backend_config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        ):
            os.environ["OPENAI_API_KEY"] = openai_key

        # Anthropic
        if anthropic_key := (
            self.backend_config.get("anthropic_api_key")
            or os.getenv("ANTHROPIC_API_KEY")
        ):
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key

        # Google
        if google_key := (
            self.backend_config.get("google_api_key") or os.getenv("GOOGLE_API_KEY")
        ):
            os.environ["GOOGLE_API_KEY"] = google_key

        # OpenRouter
        if openrouter_key := (
            self.backend_config.get("openrouter_api_key")
            or os.getenv("OPENROUTER_API_KEY")
        ):
            os.environ["OPENROUTER_API_KEY"] = openrouter_key

    @property
    def name(self) -> str:
        """Backend name for identification."""
        return "cloud"

    @property
    def is_available(self) -> bool:
        """Check if the cloud backend is available (always True since it's installed)."""
        # The cloud backend is always "available" as a backend option
        # Individual providers may or may not be configured
        return True

    @property
    def supports_streaming(self) -> bool:
        """Check if backend supports streaming."""
        return True
    
    @property
    def supports_messages(self) -> bool:
        """Check if backend supports message history format."""
        return True

    async def ask(
        self,
        prompt: Union[str, List[Union[str, ImageInput]]],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List] = None,
        **kwargs,
    ) -> AIResponse:
        """
        Send a single prompt to a cloud provider and get a complete response.

        Args:
            prompt: The user prompt - can be a string or list of content (text/images)
            model: Specific model to use (optional)
            system: System prompt (optional)
            temperature: Sampling temperature (optional)
            max_tokens: Maximum tokens to generate (optional)
            **kwargs: Additional parameters

        Returns:
            AIResponse containing the response and metadata
        """
        start_time = time.time()
        used_model = model or self.default_model

        # Build messages
        # Check if we received pre-built messages from chat session
        if 'messages' in kwargs and kwargs['messages']:
            messages = kwargs['messages']
        else:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})

            # Handle multi-modal content
            if isinstance(prompt, str):
                messages.append({"role": "user", "content": prompt})
            else:
                # Build content array for multi-modal input
                content = []
                for item in prompt:
                    if isinstance(item, str):
                        content.append({"type": "text", "text": item})
                    elif isinstance(item, ImageInput):
                        # Format image for the provider
                        if item.is_url:
                            content.append(
                                {"type": "image_url", "image_url": {"url": item.source}}
                            )
                        else:
                            # Base64 encode for non-URL images
                            base64_data = item.to_base64()
                            mime_type = item.get_mime_type()
                            content.append(
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{base64_data}"
                                    },
                                }
                            )
                messages.append({"role": "user", "content": content})

        # Build parameters
        params = {
            "model": used_model,
            "messages": messages,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        # Add tools if provided
        tool_definitions = []
        tool_result = None
        if tools:
            # Import tools here to avoid circular imports
            from ..tools import resolve_tools

            # Resolve tools to ToolDefinition objects
            resolved_tools = resolve_tools(tools)

            # Convert to LiteLLM format
            tool_definitions = []
            for tool_def in resolved_tools:
                tool_definitions.append(tool_def.to_openai_schema())

            if tool_definitions:
                params["tools"] = tool_definitions
                params["tool_choice"] = "auto"  # Let the model decide when to use tools

        # Add any additional parameters, filtering out None values
        # Also remove 'messages' from kwargs since we build it ourselves
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None and k != 'messages'}
        params.update(filtered_kwargs)

        try:
            logger.debug(f"Sending request to {used_model}")
            logger.debug(f"Parameters: max_tokens={params.get('max_tokens')}, temperature={params.get('temperature')}")

            # Use LiteLLM's completion function
            response = await self.litellm.acompletion(**params)

            # Extract response content
            if not response.choices:
                raise EmptyResponseError(used_model, self.name)

            content = response.choices[0].message.content or ""

            # Handle tool calls if present
            message = response.choices[0].message
            if hasattr(message, "tool_calls") and message.tool_calls:
                # Import tool execution here to avoid circular imports
                from ..tools import execute_tools

                # Build tool calls data
                tool_calls_data = []

                for tool_call in message.tool_calls:
                    if tool_call.type == "function":
                        func_call = tool_call.function
                        try:
                            arguments = (
                                json.loads(func_call.arguments)
                                if func_call.arguments
                                else {}
                            )
                        except json.JSONDecodeError:
                            arguments = {}

                        tool_calls_data.append(
                            {
                                "id": tool_call.id,
                                "name": func_call.name,
                                "arguments": arguments,
                            }
                        )

                # Execute tool calls
                if tool_calls_data and tools:
                    # The new executor doesn't need tool definitions map
                    tool_result = await execute_tools(tool_calls_data, parallel=True)

                    # Update content with tool results if content is empty
                    if not content:
                        # Generate a response based on tool results
                        results_summary = []
                        for call in tool_result.calls:
                            if call.succeeded:
                                results_summary.append(f"{call.name}: {call.result}")
                            else:
                                results_summary.append(
                                    f"{call.name}: Error - {call.error}"
                                )
                        content = "Tool execution completed:\n" + "\n".join(
                            results_summary
                        )

            if not content:
                raise EmptyResponseError(used_model, self.name)

            time_taken = time.time() - start_time

            # Extract usage information
            usage = response.usage
            tokens_in = usage.prompt_tokens if usage else None
            tokens_out = usage.completion_tokens if usage else None

            # Calculate cost if available
            cost = None
            if hasattr(response, "_hidden_params"):
                try:
                    if (
                        isinstance(response._hidden_params, dict)
                        and "response_cost" in response._hidden_params
                    ):
                        cost = response._hidden_params["response_cost"]
                except (TypeError, AttributeError):
                    # Handle mocks or other non-dict types
                    pass

            return AIResponse(
                content,
                model=used_model,
                backend=self.name,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                time_taken=time_taken,
                tool_result=tool_result,
                cost=cost,
                metadata={
                    "provider": self._get_provider_from_model(used_model),
                    "finish_reason": response.choices[0].finish_reason,
                },
            )

        except EmptyResponseError:
            # Re-raise EmptyResponseError as-is
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Cloud request failed: {error_msg}")

            # Check for specific error types
            if (
                "api_key" in error_msg.lower()
                or "api key" in error_msg.lower()
                or "authentication" in error_msg.lower()
            ):
                provider = self._get_provider_from_model(used_model)
                env_vars = {
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                    "google": "GOOGLE_API_KEY",
                }
                raise APIKeyError(provider, env_vars.get(provider))
            elif "rate limit" in error_msg.lower():
                provider = self._get_provider_from_model(used_model)
                raise RateLimitError(provider)
            elif "quota" in error_msg.lower():
                provider = self._get_provider_from_model(used_model)
                raise QuotaExceededError(provider)
            elif (
                "model_not_found" in error_msg.lower()
                or "does not exist" in error_msg.lower()
                or "not found" in error_msg.lower()
            ):
                raise ModelNotFoundError(used_model, self.name)
            elif "timeout" in error_msg.lower():
                raise BackendTimeoutError(self.name, self.timeout)
            else:
                raise BackendConnectionError(self.name, e)

    async def astream(
        self,
        prompt: Union[str, List[Union[str, ImageInput]]],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream a response from a cloud provider token by token.

        Args:
            prompt: The user prompt - can be a string or list of content (text/images)
            model: Specific model to use (optional)
            system: System prompt (optional)
            temperature: Sampling temperature (optional)
            max_tokens: Maximum tokens to generate (optional)
            **kwargs: Additional parameters

        Yields:
            Response chunks as they arrive
        """
        used_model = model or self.default_model

        # Build messages
        messages = []
        if system:
            messages.append({"role": "system", "content": system})

        # Handle multi-modal content (same as ask method)
        if isinstance(prompt, str):
            messages.append({"role": "user", "content": prompt})
        else:
            # Build content array for multi-modal input
            content = []
            for item in prompt:
                if isinstance(item, str):
                    content.append({"type": "text", "text": item})
                elif isinstance(item, ImageInput):
                    # Format image for the provider
                    if item.is_url:
                        content.append(
                            {"type": "image_url", "image_url": {"url": item.source}}
                        )
                    else:
                        # Base64 encode for non-URL images
                        base64_data = item.to_base64()
                        mime_type = item.get_mime_type()
                        content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_data}"
                                },
                            }
                        )
            messages.append({"role": "user", "content": content})

        # Build parameters
        params = {
            "model": used_model,
            "messages": messages,
            "stream": True,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        # Add tools if provided (same as ask method)
        if tools:
            # Import tools here to avoid circular imports
            from ..tools import resolve_tools

            # Resolve tools to ToolDefinition objects
            resolved_tools = resolve_tools(tools)

            # Convert to LiteLLM format
            tool_definitions = []
            for tool_def in resolved_tools:
                tool_definitions.append(tool_def.to_openai_schema())

            if tool_definitions:
                params["tools"] = tool_definitions
                params["tool_choice"] = "auto"

        # Add any additional parameters, filtering out None values
        # Also remove 'messages' from kwargs since we build it ourselves
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None and k != 'messages'}
        params.update(filtered_kwargs)

        try:
            logger.debug(f"Starting stream request to {used_model}")
            logger.debug(f"Stream parameters: max_tokens={params.get('max_tokens')}, temperature={params.get('temperature')}")

            # Use LiteLLM's streaming completion
            response = await self.litellm.acompletion(**params)

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Streaming request failed: {error_msg}")

            # Apply same error handling as ask method
            if (
                "api_key" in error_msg.lower()
                or "api key" in error_msg.lower()
                or "authentication" in error_msg.lower()
            ):
                provider = self._get_provider_from_model(used_model)
                env_vars = {
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                    "google": "GOOGLE_API_KEY",
                }
                raise APIKeyError(provider, env_vars.get(provider))
            elif "rate limit" in error_msg.lower():
                provider = self._get_provider_from_model(used_model)
                raise RateLimitError(provider)
            elif "quota" in error_msg.lower():
                provider = self._get_provider_from_model(used_model)
                raise QuotaExceededError(provider)
            elif (
                "model_not_found" in error_msg.lower()
                or "does not exist" in error_msg.lower()
                or "not found" in error_msg.lower()
            ):
                raise ModelNotFoundError(used_model, self.name)
            elif "timeout" in error_msg.lower():
                raise BackendTimeoutError(self.name, self.timeout)
            else:
                raise BackendConnectionError(self.name, e)

    async def models(self) -> List[str]:
        """
        Get list of available models from the central model registry.
        This backend supports all non-local models.

        Returns:
            List of model names available on cloud providers
        """
        # Get all model definitions from the registry
        all_model_info = model_registry.models.values()
        
        # Filter for models that are NOT from the 'local' provider
        cloud_models = [
            model.name for model in all_model_info if model.provider != "local"
        ]
        logger.debug(f"Found {len(cloud_models)} cloud models in registry")
        return sorted(cloud_models)

    async def list_models(
        self, detailed: bool = False
    ) -> List[Union[str, Dict[str, Any]]]:
        """
        List available models from the registry, optionally with details.

        Args:
            detailed: Whether to return detailed model information

        Returns:
            List of model names or detailed model information
        """
        # Get all non-local models from the registry
        all_model_info = [
            model for model in model_registry.models.values() if model.provider != "local"
        ]

        if not detailed:
            return sorted([model.name for model in all_model_info])

        # Return detailed information directly from the model info objects
        detailed_models = []
        for model in sorted(all_model_info, key=lambda m: m.name):
            detailed_models.append(
                {
                    "name": model.name,
                    "provider": model.provider,
                    "capabilities": model.capabilities,
                    "speed": model.speed,
                    "quality": model.quality,
                    "context_length": model.context_length,
                }
            )
        return detailed_models

    # Removed _get_provider_for_model and _get_capabilities_for_model
    # This logic is now handled by the ModelInfo dataclass in the registry

    async def status(self, test_connection: bool = False) -> Dict[str, Any]:
        """
        Get status information for cloud providers.

        Args:
            test_connection: Whether to test actual connectivity (optional)

        Returns:
            Dictionary containing status information
        """
        providers = {}

        # Check OpenAI
        if os.getenv("OPENAI_API_KEY"):
            providers["openai"] = {"available": True, "configured": True, "models": 4}
        else:
            providers["openai"] = {
                "available": False,
                "configured": False,
                "error": "OPENAI_API_KEY not configured",
            }

        # Check Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            providers["anthropic"] = {
                "available": True,
                "configured": True,
                "models": 3,
            }
        else:
            providers["anthropic"] = {
                "available": False,
                "configured": False,
                "error": "ANTHROPIC_API_KEY not configured",
            }

        # Check Google
        if os.getenv("GOOGLE_API_KEY"):
            providers["google"] = {"available": True, "configured": True, "models": 2}
        else:
            providers["google"] = {
                "available": False,
                "configured": False,
                "error": "GOOGLE_API_KEY not configured",
            }

        # If test_connection is True, perform actual connection tests
        if test_connection:
            for provider, info in providers.items():
                if info.get("configured", False):
                    # Test the connection by making a small API call
                    try:
                        test_model = self.default_models.get(provider)
                        if test_model:
                            # Make a minimal test request
                            test_response = await self.ask(
                                "Hello", model=test_model, max_tokens=5
                            )
                            if test_response and not test_response.failed:
                                info["test_result"] = "success"
                            else:
                                info["test_result"] = "failed"
                                info["test_error"] = (
                                    str(test_response.error)
                                    if test_response
                                    else "No response"
                                )
                    except Exception as e:
                        info["test_result"] = "failed"
                        info["test_error"] = str(e)

        total_models = sum(
            p.get("models", 0) for p in providers.values() if p.get("available", False)
        )

        return {
            "backend": self.name,
            "available": self.is_available,
            "providers": providers,
            "total_models": total_models,
            "default_model": self.default_model,
        }

    def _get_provider_from_model(self, model: str) -> str:
        """Determine the provider from the model name."""
        if model.startswith("gpt-"):
            return "openai"
        elif model.startswith("claude-"):
            return "anthropic"
        elif model.startswith("gemini-"):
            return "google"
        else:
            return "unknown"
