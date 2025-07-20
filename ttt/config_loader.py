"""Configuration loader utility for easy access to project config values."""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .utils import get_logger

logger = get_logger(__name__)

# Cache for project config
_project_config_cache: Optional[Dict[str, Any]] = None

# Check if we should suppress warnings (JSON mode)
import os
_suppress_warnings = os.environ.get('TTT_JSON_MODE', '').lower() == 'true'

def set_suppress_warnings(suppress: bool) -> None:
    """Set whether to suppress warnings (used in JSON mode)."""
    global _suppress_warnings
    _suppress_warnings = suppress


def get_project_config() -> Dict[str, Any]:
    """
    Get the project configuration from config.yaml.

    This function caches the configuration to avoid repeated file reads.

    Returns:
        Dictionary containing project configuration
    """
    global _project_config_cache

    if _project_config_cache is not None:
        return _project_config_cache

    # Try to find the project config.yaml
    config_paths = [
        Path(__file__).parent.parent / "config.yaml",  # Relative to ai package
        Path.cwd() / "config.yaml",  # Current working directory
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    _project_config_cache = yaml.safe_load(f)
                    logger.debug(f"Loaded project config from {config_path}")
                    return _project_config_cache
            except Exception as e:
                import os
                if os.environ.get('TTT_JSON_MODE', '').lower() != 'true':
                    logger.warning(f"Failed to load project config from {config_path}: {e}")

    # Return empty dict if no config found
    # Check suppress warnings both from variable and environment
    import os
    json_mode = os.environ.get('TTT_JSON_MODE', '').lower() == 'true'
    if not _suppress_warnings and not json_mode:
        logger.warning("Project config.yaml not found")
    _project_config_cache = {}
    return _project_config_cache


def get_config_value(path: str, default: Any = None) -> Any:
    """
    Get a configuration value by path (dot-separated).

    Args:
        path: Dot-separated path to the config value (e.g., "tools.max_file_size")
        default: Default value if path not found

    Returns:
        Configuration value or default

    Example:
        >>> get_config_value("tools.max_file_size", 10485760)
        10485760
        >>> get_config_value("backends.cloud.timeout", 30)
        30
    """
    config = get_project_config()

    keys = path.split(".")
    value = config

    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default
