"""Configuration system for the AI library."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dotenv import load_dotenv

from .models import ConfigModel, ModelInfo
from .utils import get_logger
from .exceptions import ConfigFileError, InvalidParameterError


logger = get_logger(__name__)

# Global configuration instance
_config: Optional[ConfigModel] = None


def get_config() -> ConfigModel:
    """
    Get the global configuration, loading it if necessary.
    
    Returns:
        ConfigModel instance with current configuration
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def load_config(config_file: Optional[Union[str, Path]] = None) -> ConfigModel:
    """
    Load configuration from multiple sources with precedence:
    1. Programmatic overrides (highest)
    2. Environment variables
    3. Config file
    4. Defaults (lowest)
    
    Args:
        config_file: Path to config file. If None, searches standard locations.
        
    Returns:
        ConfigModel instance with loaded configuration
    """
    # Load .env file if it exists
    load_dotenv()
    
    # Start with defaults
    config_data = {}
    models_data = []
    
    # Load from config file if specified or found
    if config_file:
        config_path = Path(config_file)
    else:
        config_path = find_config_file()
    
    if config_path and config_path.exists():
        try:
            with open(config_path) as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    file_config = yaml.safe_load(f)
                else:
                    raise ConfigFileError(str(config_path), f"Unsupported config file format: {config_path.suffix}")
            
            if file_config:
                # Extract models separately
                if 'models' in file_config:
                    models_data = file_config.pop('models', [])
                
                config_data.update(file_config)
                logger.debug(f"Loaded config from {config_path}")
        except yaml.YAMLError as e:
            raise ConfigFileError(str(config_path), f"YAML parsing error: {e}")
        except Exception as e:
            raise ConfigFileError(str(config_path), str(e))
    
    # Override with environment variables
    import os
    env_mappings = {
        'openai_api_key': 'OPENAI_API_KEY',
        'anthropic_api_key': 'ANTHROPIC_API_KEY', 
        'google_api_key': 'GOOGLE_API_KEY',
        'ollama_base_url': 'OLLAMA_BASE_URL',
        'default_backend': 'AI_DEFAULT_BACKEND',
        'default_model': 'AI_DEFAULT_MODEL',
        'timeout': 'AI_TIMEOUT',
        'max_retries': 'AI_MAX_RETRIES',
        'enable_fallbacks': 'AI_ENABLE_FALLBACKS'
    }
    
    for config_key, env_key in env_mappings.items():
        env_value = os.getenv(env_key)
        if env_value is not None:
            # Handle type conversion for non-string values
            if config_key in ['timeout', 'max_retries']:
                try:
                    config_data[config_key] = int(env_value)
                except ValueError:
                    logger.warning(f"Invalid integer value for {env_key}: {env_value}")
            elif config_key == 'enable_fallbacks':
                config_data[config_key] = env_value.lower() in ('true', '1', 'yes', 'on')
            else:
                config_data[config_key] = env_value
    
    # Create ConfigModel with resolved configuration
    config = ConfigModel(**config_data)
    
    # Load custom models into registry
    if models_data:
        for model_data in models_data:
            try:
                model = ModelInfo(**model_data)
                model_registry.add_model(model)
                logger.debug(f"Loaded custom model: {model.name}")
            except Exception as e:
                logger.warning(f"Failed to load model definition: {e}")
    
    return config


def find_config_file() -> Optional[Path]:
    """
    Find configuration file in standard locations.
    
    Returns:
        Path to config file if found, None otherwise
    """
    search_paths = [
        Path.cwd() / "ai.yaml",
        Path.cwd() / "ai.yml", 
        Path.cwd() / ".ai.yaml",
        Path.cwd() / ".ai.yml",
        Path.home() / ".config" / "ai" / "config.yaml",
        Path.home() / ".config" / "ai" / "config.yml",
        Path.home() / ".ai.yaml",
        Path.home() / ".ai.yml",
    ]
    
    for path in search_paths:
        if path.exists():
            logger.debug(f"Found config file: {path}")
            return path
    
    logger.debug("No config file found")
    return None


def save_config(config: ConfigModel, config_file: Optional[Union[str, Path]] = None) -> None:
    """
    Save configuration to file.
    
    Args:
        config: ConfigModel instance to save
        config_file: Path to save to. If None, uses default location.
    """
    if config_file:
        config_path = Path(config_file)
    else:
        # Default to user config directory
        config_path = Path.home() / ".config" / "ai" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert config to dict, excluding sensitive data
    config_dict = config.model_dump(exclude={
        "openai_api_key",
        "anthropic_api_key", 
        "google_api_key"
    })
    
    try:
        with open(config_path, 'w') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False)
        logger.info(f"Saved config to {config_path}")
    except Exception as e:
        raise ConfigFileError(str(config_path), f"Failed to save: {e}")


def configure(
    *,
    openai_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    google_api_key: Optional[str] = None,
    ollama_base_url: Optional[str] = None,
    default_backend: Optional[str] = None,
    default_model: Optional[str] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
    **kwargs
) -> None:
    """
    Configure the AI library programmatically.
    
    This function allows you to set configuration options at runtime,
    overriding any file or environment-based configuration.
    
    Args:
        openai_api_key: OpenAI API key
        anthropic_api_key: Anthropic API key
        google_api_key: Google API key
        ollama_base_url: Ollama base URL
        default_backend: Default backend to use
        default_model: Default model to use
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
        **kwargs: Additional configuration options
    """
    global _config
    
    # Load current config
    current_config = get_config()
    
    # Build update dict
    updates = {}
    
    if openai_api_key is not None:
        updates["openai_api_key"] = openai_api_key
    if anthropic_api_key is not None:
        updates["anthropic_api_key"] = anthropic_api_key
    if google_api_key is not None:
        updates["google_api_key"] = google_api_key
    if ollama_base_url is not None:
        updates["ollama_base_url"] = ollama_base_url
    if default_backend is not None:
        updates["default_backend"] = default_backend
    if default_model is not None:
        updates["default_model"] = default_model
    if timeout is not None:
        updates["timeout"] = timeout
    if max_retries is not None:
        updates["max_retries"] = max_retries
    
    # Add any additional kwargs
    updates.update(kwargs)
    
    # Create new config with updates
    config_dict = current_config.model_dump()
    config_dict.update(updates)
    
    _config = ConfigModel(**config_dict)
    logger.debug("Configuration updated programmatically")


class ModelRegistry:
    """
    Registry for managing model information and aliases.
    """
    
    def __init__(self):
        self.models: Dict[str, ModelInfo] = {}
        self.aliases: Dict[str, str] = {}
        self._load_default_models()
    
    def _load_default_models(self) -> None:
        """Load default model configurations."""
        # OpenAI models
        self.add_model(ModelInfo(
            name="gpt-4",
            provider="openai",
            provider_name="gpt-4",
            aliases=["best", "quality"],
            speed="slow",
            quality="high",
            capabilities=["text", "reasoning"],
            context_length=8192
        ))
        
        self.add_model(ModelInfo(
            name="gpt-3.5-turbo",
            provider="openai", 
            provider_name="gpt-3.5-turbo",
            aliases=["fast", "cheap"],
            speed="fast",
            quality="medium",
            capabilities=["text", "chat"],
            context_length=4096
        ))
        
        self.add_model(ModelInfo(
            name="gpt-4-vision-preview",
            provider="openai",
            provider_name="gpt-4-vision-preview",
            aliases=["vision", "gpt-vision"],
            speed="slow",
            quality="high",
            capabilities=["text", "reasoning", "vision"],
            context_length=128000
        ))
        
        # Anthropic models
        self.add_model(ModelInfo(
            name="claude-3-opus",
            provider="anthropic",
            provider_name="claude-3-opus-20240229",
            aliases=["claude-best", "opus"],
            speed="slow",
            quality="high",
            capabilities=["text", "reasoning", "code", "vision"],
            context_length=200000
        ))
        
        self.add_model(ModelInfo(
            name="claude-3-sonnet",
            provider="anthropic",
            provider_name="claude-3-sonnet-20240229",
            aliases=["coding", "analysis", "claude"],
            speed="medium",
            quality="high",
            capabilities=["text", "reasoning", "code"],
            context_length=200000
        ))
        
        self.add_model(ModelInfo(
            name="claude-3-haiku",
            provider="anthropic",
            provider_name="claude-3-haiku-20240307",
            aliases=["claude-fast", "haiku"],
            speed="fast",
            quality="medium",
            capabilities=["text", "chat"],
            context_length=200000
        ))
        
        # Google models
        self.add_model(ModelInfo(
            name="gemini-pro",
            provider="google",
            provider_name="gemini-pro",
            aliases=["gemini", "google"],
            speed="medium",
            quality="high",
            capabilities=["text", "reasoning"],
            context_length=30720
        ))
        
        self.add_model(ModelInfo(
            name="gemini-pro-vision",
            provider="google",
            provider_name="gemini-pro-vision",
            aliases=["gemini-vision"],
            speed="medium",
            quality="high",
            capabilities=["text", "reasoning", "vision"],
            context_length=30720
        ))
        
        # Local models (common ones)
        self.add_model(ModelInfo(
            name="llama2",
            provider="local",
            provider_name="llama2",
            aliases=["local", "private"],
            speed="medium",
            quality="medium",
            capabilities=["text", "chat"],
            context_length=4096
        ))
        
        self.add_model(ModelInfo(
            name="mistral",
            provider="local",
            provider_name="mistral",
            aliases=["mistral-local"],
            speed="fast",
            quality="medium",
            capabilities=["text", "chat"],
            context_length=8192
        ))
        
        self.add_model(ModelInfo(
            name="codellama",
            provider="local",
            provider_name="codellama",
            aliases=["local-code"],
            speed="medium",
            quality="medium",
            capabilities=["code", "text"],
            context_length=4096
        ))
    
    def add_model(self, model: ModelInfo) -> None:
        """Add a model to the registry."""
        self.models[model.name] = model
        
        # Register aliases
        for alias in model.aliases or []:
            self.aliases[alias] = model.name
    
    def get_model(self, name_or_alias: str) -> Optional[ModelInfo]:
        """Get model info by name or alias."""
        # Try direct name first
        if name_or_alias in self.models:
            return self.models[name_or_alias]
        
        # Try alias
        if name_or_alias in self.aliases:
            real_name = self.aliases[name_or_alias]
            return self.models.get(real_name)
        
        return None
    
    def resolve_model_name(self, name_or_alias: str) -> str:
        """Resolve an alias to the actual model name."""
        if name_or_alias in self.aliases:
            return self.aliases[name_or_alias]
        return name_or_alias
    
    def list_models(self, provider: Optional[str] = None) -> List[str]:
        """List available models, optionally filtered by provider."""
        models = []
        for name, model in self.models.items():
            if provider is None or model.provider == provider:
                models.append(name)
        return sorted(models)
    
    def list_aliases(self) -> Dict[str, str]:
        """List all aliases and their target models."""
        return dict(self.aliases)


# Global model registry
model_registry = ModelRegistry()