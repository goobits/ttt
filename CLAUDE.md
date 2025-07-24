# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Information

**Package**: `goobits-ttt` (PyPI) | **Command**: `ttt` | **Version**: 1.0.0rc4 | **Python**: 3.8+

## Development Commands

### Test Commands
- `./test.sh` - Run unit tests (free, fast, default)
- `./test.sh integration` - Run integration tests (costs money, requires API keys)
- `./test.sh all` - Run unit tests first, then integration tests
- `./test.sh unit --coverage` - Run unit tests with coverage report
- `./test.sh --test test_api` - Run specific test file
- `./test.sh --markers "not slow"` - Skip slow tests

### Linting and Code Quality
- `ruff src/ttt/ tests/` - Run ruff linter
- `black src/ttt/ tests/` - Format code
- `mypy src/ttt/` - Type checking

### Installation and Setup
- `./setup.sh install` - Install with pipx (for end users)
- `./setup.sh install --dev` - Install in development mode with pipx --editable (RECOMMENDED FOR DEVELOPMENT)
- `./setup.sh upgrade` - Upgrade to latest version  
- `./setup.sh uninstall` - Remove the TTT library

**IMPORTANT FOR DEVELOPMENT**: Always use `./setup.sh install --dev` for development work. This creates an editable installation where code changes are immediately reflected without needing to reinstall or upgrade.

### CLI Testing
- `ttt` - Show help menu
- `ttt "test question"` - Basic functionality test (direct prompt syntax)
- `ttt status` - Check backend connectivity
- `ttt models` - List available models
- `ttt config` - Show configuration settings

## Architecture Overview

This is a unified AI library that provides both CLI and Python API access to multiple AI providers through a backend abstraction system.

### Core Architecture Pattern
```
CLI Interface / Python API
         ↓
    Backend Abstraction Layer (src/ttt/backends/)
         ↓
    AI Providers (OpenRouter, OpenAI, Anthropic, Google, Ollama)
```

### Key Components

**API Layer** (`src/ttt/api.py`): Main interface with `ask()` and `stream()` functions
- Synchronous and asynchronous APIs
- Unified interface across all providers
- Response objects with metadata

**Backend System** (`src/ttt/backends/`):
- `cloud.py` - Cloud provider backend using LiteLLM
- `local.py` - Local Ollama backend for privacy
- `base.py` - Abstract backend interface

**Routing System** (`src/ttt/routing.py`):
- Automatic backend selection based on model patterns
- Model registry with provider mappings
- Fallback mechanisms between providers

**Tool System** (`src/ttt/tools/`):
- Function calling with automatic schema generation
- Built-in tools (web_search, file operations, code execution)
- Custom tool registration via decorators

**CLI Interface** (`src/ttt/cli.py`):
- Direct command execution: `ttt "question"`
- Pipe support: `echo "text" | ttt`
- Rich terminal output with error handling

**Configuration System** (`src/ttt/config.py`, `src/ttt/config_loader.py`):
- Hierarchical config loading (env vars, YAML files)
- Default configuration in `config.yaml`
- Runtime configuration management

### Key Files

**Entry Points:**
- `src/ttt/__main__.py` - CLI entry point
- `src/ttt/__init__.py` - Public API exports
- `src/ttt/cli.py` - CLI command definitions

**Core Logic:**
- `src/ttt/api.py` - Main ask/stream/chat functions
- `src/ttt/routing.py` - Model/backend routing logic
- `src/ttt/models.py` - Model definitions and metadata
- `src/ttt/exceptions.py` - Custom exception classes

**Supporting:**
- `src/ttt/cli.py` - Auto-generated CLI entry point
- `src/ttt/app_hooks.py` - Custom CLI hooks and formatters
- `config.yaml` - Default configuration with model registry

## Testing

### IMPORTANT: Test Execution

**Always use `./test.sh` for tests** - DO NOT run `pytest` directly for integration tests as it bypasses critical rate limiting.

```bash
# Unit tests (default, free, fast)
./test.sh                      # Run unit tests
./test.sh unit --coverage      # With coverage report

# Integration tests (costs money, requires API keys)
source .env && export OPENROUTER_API_KEY
./test.sh integration          # Will prompt for confirmation
./test.sh integration --force  # Skip confirmation

# Custom rate limiting for strict APIs
OPENROUTER_RATE_DELAY=2.0 ./test.sh integration --force
```

The test.sh script ensures proper rate limiting, validates API keys, and separates test types to prevent unexpected costs.

## Configuration

### Model Routing
- Cloud models: Patterns like `openrouter/`, `gpt-`, `claude-`, `gemini-`
- Local models: Assumes Ollama for non-cloud patterns
- Default model: `openrouter/google/gemini-flash-1.5`
- Model aliases: `fast`, `best`, `cheap`, `coding`, `local` (defined in config.yaml)

### API Keys (Environment Variables)
- `OPENROUTER_API_KEY` - Recommended (access to 100+ models)
- `OPENAI_API_KEY` - Direct OpenAI access
- `ANTHROPIC_API_KEY` - Direct Anthropic access
- `GOOGLE_API_KEY` - Direct Google access
- `OLLAMA_BASE_URL` - Local Ollama URL (default: http://localhost:11434)

### Configuration Files
The library searches for configuration in this order:
1. `./ttt.yaml` or `./ttt.yml` - Project-specific config
2. `./.ttt.yaml` or `./.ttt.yml` - Hidden project config
3. `~/.config/ttt/config.yaml` or `~/.config/ttt/config.yml` - User config
4. `~/.ttt.yaml` or `~/.ttt.yml` - Hidden user config
5. `config.yaml` - Default configuration (built-in)
6. `.env` - Environment variables and API keys

## Development Guidelines

### Code Style
- Black formatting (line length: 88)
- Ruff linting (checks: E, W, F, I, B, C4, UP; ignores: E501, B008, C901)
- MyPy type checking (strict mode)
- Follow existing patterns in similar files


### Tool Development
- Use `@tool` decorator from `src/ttt/tools/base.py`
- Include comprehensive docstrings for schema generation
- Test security implications for code execution tools
- Follow existing patterns in `src/ttt/tools/builtins.py`

### Temporary Files
When creating temporary debug or test scripts, use `/tmp` directory to keep the project clean.

## Built-in Tools

The project includes these built-in tools (in `src/ttt/tools/builtins.py`):
- `web_search` - Search the web for information
- `read_file` - Read contents of a file
- `write_file` - Write content to a file
- `list_directory` - List files in a directory
- `run_python` - Execute Python code safely
- `get_current_time` - Get current time in any timezone
- `http_request` - Make HTTP API requests
- `calculate` - Perform mathematical calculations

## Plugin System

Plugin discovery locations (in order):
1. `~/.config/ttt/plugins/`
2. `~/.ai/plugins/`
3. `./ai_plugins/`
4. Built-in plugins directory

Plugins must have a `register_plugin(registry)` function.

## CLI Generation

The project uses a unique CLI generation system:
- `src/ttt/cli.py` - Auto-generated from goobits.yaml
- `src/ttt/app_hooks.py` - Custom formatters and hooks
- Generation occurs via goobits build command during development