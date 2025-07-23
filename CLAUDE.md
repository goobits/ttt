# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Test Commands
- `./test.sh` - Run unit tests (free, fast, default)
- `./test.sh integration` - Run integration tests (costs money, requires API keys)
- `./test.sh all` - Run unit tests first, then integration tests
- `./test.sh unit --coverage` - Run unit tests with coverage report
- `./test.sh --test test_api` - Run specific test file
- `./test.sh --markers "not slow"` - Skip slow tests

### Linting and Code Quality
- `ruff src/ttt/ tests/` - Run ruff linter (install with: `pip install ruff`)
- `black src/ttt/ tests/` - Format code with black (install with: `pip install black`)
- `mypy src/ttt/` - Type checking (install with: `pip install mypy`)

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
    Backend Abstraction Layer (ai/backends/)
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
- `src/ttt/chat.py` - Chat session management  
- `src/ttt/plugins.py` - Plugin system for extensions
- `config.yaml` - Default configuration with model registry

## Testing Patterns

### Test Structure
- **Unit Tests**: Free, mocked, no API costs (default)
- **Integration Tests**: Real API calls, costs money, requires API keys
- **Rate Limiting**: Automatic delays between API calls in integration tests

### Key Test Files
- `tests/test_builtin_tools.py` - Tool testing with security validation
- `tests/test_local_backend.py` - Backend testing with httpx mocking
- `tests/test_modern_cli.py` - CLI testing with Click's CliRunner
- `tests/test_integration.py` - Integration tests with real APIs

### Test Execution Tips
- Always run unit tests first before integration tests
- Use `--markers "not slow"` to skip time-intensive tests
- Integration tests require API keys and will prompt for confirmation
- Rate limiting is built into integration tests via conftest.py

### IMPORTANT: Proper Test Execution

**DO NOT run tests directly with `pytest` for integration tests!** The test suite has built-in rate limiting that must be used properly.

#### Correct Way to Run Tests:

1. **Unit Tests (recommended for development)**:
   ```bash
   ./test.sh unit              # Run all unit tests
   ./test.sh                   # Same as above (unit is default)
   ./test.sh unit --coverage   # With coverage report
   ```

2. **Integration Tests (requires API keys)**:
   ```bash
   # First export API keys from .env if needed
   source .env && export OPENROUTER_API_KEY
   
   # Run with built-in delays
   ./test.sh integration       # Will prompt for confirmation
   ./test.sh integration --force  # Skip confirmation
   
   # With custom delay (recommended for rate-limited APIs)
   OPENROUTER_RATE_DELAY=2.0 ./test.sh integration --force
   ```

3. **All Tests**:
   ```bash
   ./test.sh all               # Runs unit tests first, then integration
   ```

#### Why Use test.sh:
- Checks for required dependencies (pytest-asyncio)
- Validates API keys before running integration tests
- Applies proper rate limiting via conftest.py fixtures
- Uses correct pytest markers to separate test types
- Provides cost warnings for integration tests

#### Rate Limiting Configuration:
The test suite uses these default delays (configurable via environment variables):
- `OPENROUTER_RATE_DELAY=1.0` (1 second between OpenRouter calls)
- `OPENAI_RATE_DELAY=0.5` (0.5 seconds between OpenAI calls)
- `ANTHROPIC_RATE_DELAY=0.5` (0.5 seconds between Anthropic calls)

Integration tests use special fixtures (`delayed_ask`, `delayed_stream`, `delayed_chat`) that automatically apply these delays to prevent rate limiting errors.

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
- `config.yaml` - Default configuration
- `~/.config/ttt/config.yaml` - User configuration
- `.env` - Environment variables and API keys

## Development Guidelines

### Code Style
- Black formatting (line length: 88)
- Ruff linting with pycodestyle, pyflakes, isort
- MyPy type checking (strict mode)
- Follow existing patterns in similar files

### Error Handling
- Custom exceptions in `src/ttt/exceptions.py`
- User-friendly error messages with actionable suggestions
- Graceful degradation with provider fallbacks

### Testing Requirements
- Unit tests for all new functionality
- Integration tests for API-dependent features
- Mock external dependencies (httpx, API calls)
- Test edge cases and error conditions

### Tool Development
- Use `@tool` decorator from `src/ttt/tools/base.py`
- Include comprehensive docstrings for schema generation
- Test security implications for code execution tools
- Follow existing patterns in `src/ttt/tools/builtins.py`

### Temporary Files
When creating temporary debug or test scripts, use `/tmp` directory to keep the project clean.