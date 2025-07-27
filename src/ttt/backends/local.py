"""Local backend implementation using Ollama."""

import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import httpx

from ..core.exceptions import (
    BackendConnectionError,
    BackendTimeoutError,
    EmptyResponseError,
    ModelNotFoundError,
    ResponseParsingError,
)
from ..core.models import AIResponse, ImageInput
from ..utils import get_logger, run_async
from .base import BaseBackend

logger = get_logger(__name__)


class LocalBackend(BaseBackend):
    """
    Local backend that communicates with Ollama for local model inference.

    This backend provides privacy-first AI by running models locally
    through the Ollama API.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the local backend.

        Args:
            config: Configuration dictionary containing base_url and other settings
        """
        super().__init__(config)
        # Get local-specific config
        local_config = self.backend_config.get("local", {})

        # Use backend_config from base class which handles merging
        from ..config.loader import get_config_value

        self.base_url = (
            local_config.get("base_url")
            or self.backend_config.get("ollama_base_url")
            or get_config_value("backends.local.base_url")
            or get_config_value("constants.urls.ollama_default", "http://localhost:11434")
        )

        self.default_model = local_config.get("default_model") or get_config_value(
            "backends.local.default_model", "llama2"
        )

    @property
    def name(self) -> str:
        """Backend name for identification."""
        return "local"

    @property
    def is_available(self) -> bool:
        """Check if Ollama is running and available."""
        try:
            # Create a simple sync check
            async def check() -> bool:
                from ..config.loader import get_config_value
                availability_timeout = get_config_value(
                    "constants.timeouts.availability_check", 5
                )
                async with httpx.AsyncClient(timeout=availability_timeout) as client:
                    response = await client.get(f"{self.base_url}/api/tags")
                    return response.status_code == 200

            # Use run_async to handle the event loop properly
            result = run_async(check())
            return bool(result)
        except Exception as e:
            logger.debug(f"Ollama availability check failed: {e}")
            return False

    async def ask(
        self,
        prompt: Union[str, List[Union[str, ImageInput]]],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> AIResponse:
        """
        Send a single prompt to Ollama and get a complete response.

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

        # Check for multi-modal input
        if not isinstance(prompt, str):
            # Check if any images are in the prompt
            has_images = any(isinstance(item, ImageInput) for item in prompt)
            if has_images:
                # Raise MultiModalError for image inputs
                from ..core.exceptions import MultiModalError

                raise MultiModalError(
                    "Local backend (Ollama) does not support image inputs yet. "
                    "Please use a cloud backend with vision capabilities."
                )
            # Extract text from the list
            prompt = " ".join(item for item in prompt if isinstance(item, str))

        # Build the request payload
        payload = {"model": used_model, "prompt": prompt, "stream": False}

        # Add optional parameters
        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        if options:
            payload["options"] = options

        # Add system prompt if provided
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Sending request to Ollama: {used_model}")

                response = await client.post(
                    f"{self.base_url}/api/generate", json=payload
                )
                response.raise_for_status()

                data = response.json()
                content = data.get("response", "")

                if not content:
                    raise EmptyResponseError(used_model, self.name)

                time_taken = time.time() - start_time

                # Extract metadata
                eval_count = data.get("eval_count", 0)
                prompt_eval_count = data.get("prompt_eval_count", 0)

                return AIResponse(
                    content,
                    model=used_model,
                    backend=self.name,
                    tokens_in=prompt_eval_count,
                    tokens_out=eval_count,
                    time_taken=time_taken,
                    metadata={
                        "eval_duration": data.get("eval_duration"),
                        "load_duration": data.get("load_duration"),
                        "total_duration": data.get("total_duration"),
                    },
                )

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(f"Ollama request failed: {error_msg}")

            # Check for specific error types
            if e.response.status_code == 404:
                if "model" in e.response.text.lower():
                    raise ModelNotFoundError(used_model, self.name) from e

            raise BackendConnectionError(self.name, e) from e
        except httpx.TimeoutException:
            raise BackendTimeoutError(self.name, self.timeout) from None
        except Exception as e:
            logger.error(f"Ollama request failed: {str(e)}")
            raise BackendConnectionError(self.name, e) from e

    async def astream(  # type: ignore[override]
        self,
        prompt: Union[str, List[Union[str, ImageInput]]],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream a response from Ollama token by token.

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

        # Check for multi-modal input
        if not isinstance(prompt, str):
            # Check if any images are in the prompt
            has_images = any(isinstance(item, ImageInput) for item in prompt)
            if has_images:
                # Raise MultiModalError for image inputs
                from ..core.exceptions import MultiModalError

                raise MultiModalError(
                    "Local backend (Ollama) does not support image inputs yet. "
                    "Please use a cloud backend with vision capabilities."
                )
            # Extract text from the list
            prompt = " ".join(item for item in prompt if isinstance(item, str))

        # Build the request payload
        payload = {"model": used_model, "prompt": prompt, "stream": True}

        # Add optional parameters
        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        if options:
            payload["options"] = options

        # Add system prompt if provided
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"Starting stream request to Ollama: {used_model}")

                async with client.stream(
                    "POST", f"{self.base_url}/api/generate", json=payload
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    chunk = data["response"]
                                    if chunk:
                                        yield chunk

                                # Check if this is the final chunk
                                if data.get("done", False):
                                    break

                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse JSON line: {line}")
                                raise ResponseParsingError(
                                    f"Invalid JSON in stream: {line[:100]}", line
                                ) from e

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404 and "model" in e.response.text.lower():
                raise ModelNotFoundError(used_model, self.name) from e
            raise BackendConnectionError(self.name, e) from e
        except httpx.TimeoutException:
            raise BackendTimeoutError(self.name, self.timeout) from None
        except Exception as e:
            logger.error(f"Streaming request failed: {str(e)}")
            raise BackendConnectionError(self.name, e) from e

    async def models(self) -> List[str]:
        """
        Get list of available models from Ollama.

        Returns:
            List of model names available locally
        """
        try:
            from ..config.loader import get_config_value
            model_list_timeout = get_config_value("constants.timeouts.model_list", 10)
            async with httpx.AsyncClient(timeout=model_list_timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()

                data = response.json()
                models = [model["name"] for model in data.get("models", [])]

                logger.debug(f"Found {len(models)} local models")
                return models

        except httpx.TimeoutException:
            from ..config.loader import get_config_value
            model_list_timeout = get_config_value("constants.timeouts.model_list", 10)
            raise BackendTimeoutError(self.name, float(model_list_timeout)) from None
        except Exception as e:
            logger.error(f"Failed to fetch models: {str(e)}")
            raise BackendConnectionError(self.name, e) from e

    async def status(self) -> Dict[str, Any]:
        """
        Get status information from Ollama.

        Returns:
            Dictionary containing status information
        """
        try:
            models = await self.models()

            return {
                "backend": self.name,
                "base_url": self.base_url,
                "available": self.is_available,
                "models_count": len(models),
                "models": models[:5],  # Show first 5 models
                "default_model": self.default_model,
            }

        except Exception as e:
            return {
                "backend": self.name,
                "base_url": self.base_url,
                "available": False,
                "error": str(e),
            }
