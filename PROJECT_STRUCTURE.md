# TTT CLI Project Structure

## Overview
TTT (Tiny AI Tools) is a unified AI library providing both CLI and Python API access to multiple AI providers through a backend abstraction system.

## Directory Structure

```
ttt/                              # Main project directory
├── __init__.py                   # Public API exports
├── __main__.py                   # CLI entry point
├── api.py                        # Main ask/stream/chat functions
├── cli.py                        # CLI command definitions using Google Fire
├── chat.py                       # Chat session management
├── chat_sessions.py              # Chat session persistence
├── config.py                     # Configuration system
├── config_loader.py              # Hierarchical config loading
├── config_manager.py             # Runtime configuration management
├── exceptions.py                 # Custom exception classes
├── models.py                     # Model definitions and metadata
├── plugins.py                    # Plugin system for extensions
├── routing.py                    # Model/backend routing logic
├── app_hooks.py                  # Application hooks
│
├── backends/                     # Backend abstraction layer
│   ├── __init__.py
│   ├── base.py                   # Abstract backend interface
│   ├── cloud.py                  # Cloud provider backend (LiteLLM)
│   └── local.py                  # Local Ollama backend
│
├── tools/                        # Tool/function calling system
│   ├── __init__.py
│   ├── base.py                   # Tool decorator and base classes
│   ├── builtins.py               # Built-in tools (web_search, file ops, etc.)
│   ├── executor.py               # Tool execution logic
│   ├── registry.py               # Tool registration system
│   └── recovery.py               # Error recovery mechanisms
│
├── utils/                        # Utility modules
│   ├── __init__.py
│   ├── async_utils.py            # Async utilities
│   ├── logger.py                 # Logging configuration
│   └── warning_capture.py        # Warning suppression utilities
│
└── shared-setup/                 # Shared setup scripts
    ├── README.md
    └── setup.sh                  # Installation script

tests/                            # Test suite
├── __init__.py
├── conftest.py                   # Pytest configuration and fixtures
├── test_api_core.py              # Core API tests
├── test_api_streaming.py         # Streaming API tests
├── test_backends_cloud.py        # Cloud backend tests
├── test_backends_local.py        # Local backend tests
├── test_chat.py                  # Chat functionality tests
├── test_cli_modern.py            # CLI tests
├── test_config.py                # Configuration tests
├── test_errors.py                # Error handling tests
├── test_integration.py           # Integration tests (requires API keys)
├── test_models.py                # Model management tests
├── test_multimodal.py            # Multimodal support tests
├── test_plugins.py               # Plugin system tests
├── test_routing.py               # Routing logic tests
├── test_tools_builtin.py         # Built-in tool tests
├── test_tools_chat.py            # Chat-specific tool tests
├── test_tools_custom.py          # Custom tool tests
├── README_TESTING.md             # Testing documentation
└── README_RATE_LIMITING.md       # Rate limiting documentation

examples/                         # Example scripts
├── 01_basic_usage.py             # Basic API usage examples
├── 02_tools_and_workflows.py     # Tool usage examples
├── 03_chat_and_persistence.py    # Chat session examples
├── 04_advanced_features.py       # Advanced features
├── README.md                     # Examples documentation
├── config/                       # Example configurations
│   ├── ai.yaml
│   └── ai-custom.yaml
└── plugins/                      # Example plugins
    ├── echo_backend.py
    ├── mock_llm_backend.py
    └── README.md

docs/                             # Documentation
├── api-reference.md              # API reference
└── extensibility.md              # Plugin development guide

Root Files:
├── pyproject.toml                # Python project configuration
├── config.yaml                   # Default configuration
├── setup.sh                      # Installation script
├── test.sh                       # Test runner script
├── README.md                     # Main documentation
├── CLAUDE.md                     # Claude Code instructions
├── TTT_CLI.md                    # CLI documentation
├── LICENSE                       # MIT License
└── FIXME.md                      # Known issues/todos
```

## Key Architecture Components

### 1. Core API Layer (`ttt/api.py`)
- Main interface with `ask()` and `stream()` functions
- Synchronous and asynchronous APIs
- Unified interface across all providers
- Response objects with metadata

### 2. Backend System (`ttt/backends/`)
- **base.py**: Abstract backend interface defining required methods
- **cloud.py**: Cloud provider backend using LiteLLM for OpenRouter, OpenAI, Anthropic, Google
- **local.py**: Local Ollama backend for privacy-focused usage

### 3. CLI Interface (`ttt/cli.py`)
- Google Fire-based CLI framework (recently migrated from Click)
- Direct command execution: `ttt "question"`
- Pipe support: `echo "text" | ttt`
- Rich terminal output with error handling

### 4. Routing System (`ttt/routing.py`)
- Automatic backend selection based on model patterns
- Model registry with provider mappings
- Fallback mechanisms between providers

### 5. Tool System (`ttt/tools/`)
- Function calling with automatic schema generation
- Built-in tools: web_search, file operations, code execution
- Custom tool registration via decorators
- Security validation for code execution

### 6. Configuration System
- **config.py**: Configuration data classes
- **config_loader.py**: Hierarchical loading (env vars, YAML files)
- **config_manager.py**: Runtime configuration management
- **config.yaml**: Default configuration with model registry

### 7. Testing Infrastructure
- Unit tests: Free, mocked, no API costs (default)
- Integration tests: Real API calls, costs money, requires API keys
- Rate limiting: Automatic delays between API calls
- Test runner: `./test.sh` with proper dependency checking

## Model Routing Patterns
- Cloud models: `openrouter/`, `gpt-`, `claude-`, `gemini-`
- Local models: Assumes Ollama for non-cloud patterns
- Default model: `openrouter/google/gemini-flash-1.5`
- Model aliases: `fast`, `best`, `cheap`, `coding`, `local`

## Recent Changes
- Migrated from Click to Google Fire CLI framework (current branch: cli-fire-migration)
- Modified files include CLI implementation, backends, and built-in tools
- Simplified CLI structure while maintaining all functionality