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
- `ruff ai/ tests/` - Run ruff linter (configured in pyproject.toml)
- `black ai/ tests/` - Format code with black
- `mypy ai/` - Type checking (strict configuration)

### Installation and Setup
- `./setup.sh install` - Install the AI library with dependencies
- `./setup.sh uninstall` - Remove the AI library
- `poetry install` - Install dependencies if Poetry is available
- `pip install -e .` - Install in development mode

### CLI Testing
- `ai` - Show help menu
- `ai "test question"` - Basic functionality test
- `ai backend-status` - Check backend connectivity
- `ai models-list` - List available models

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

**API Layer** (`ai/api.py`): Main interface with `ask()` and `stream()` functions
- Synchronous and asynchronous APIs
- Unified interface across all providers
- Response objects with metadata

**Backend System** (`ai/backends/`):
- `cloud.py` - Cloud provider backend using LiteLLM
- `local.py` - Local Ollama backend for privacy
- `base.py` - Abstract backend interface

**Routing System** (`ai/routing.py`):
- Automatic backend selection based on model patterns
- Model registry with provider mappings
- Fallback mechanisms between providers

**Tool System** (`ai/tools/`):
- Function calling with automatic schema generation
- Built-in tools (web_search, file operations, code execution)
- Custom tool registration via decorators

**CLI Interface** (`ai/cli.py`):
- Direct command execution: `ai "question"`
- Pipe support: `echo "text" | ai`
- Rich terminal output with error handling

**Configuration System** (`ai/config.py`, `ai/config_loader.py`):
- Hierarchical config loading (env vars, YAML files)
- Default configuration in `config.yaml`
- Runtime configuration management

### Key Files

**Entry Points:**
- `ai/__main__.py` - CLI entry point
- `ai/__init__.py` - Public API exports
- `ai/cli.py` - CLI command definitions

**Core Logic:**
- `ai/api.py` - Main ask/stream/chat functions
- `ai/routing.py` - Model/backend routing logic
- `ai/models.py` - Model definitions and metadata
- `ai/exceptions.py` - Custom exception classes

**Supporting:**
- `ai/chat.py` - Chat session management
- `ai/plugins.py` - Plugin system for extensions

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

### API Keys (Environment Variables)
- `OPENROUTER_API_KEY` - Recommended (access to 100+ models)
- `OPENAI_API_KEY` - Direct OpenAI access
- `ANTHROPIC_API_KEY` - Direct Anthropic access
- `GOOGLE_API_KEY` - Direct Google access
- `OLLAMA_BASE_URL` - Local Ollama URL (default: http://localhost:11434)

### Configuration Files
- `config.yaml` - Default configuration
- `~/.config/ai/config.yaml` - User configuration
- `.env` - Environment variables and API keys

## Development Guidelines

### Code Style
- Black formatting (line length: 88)
- Ruff linting with pycodestyle, pyflakes, isort
- MyPy type checking (strict mode)
- Follow existing patterns in similar files

### Error Handling
- Custom exceptions in `ai/exceptions.py`
- User-friendly error messages with actionable suggestions
- Graceful degradation with provider fallbacks

### Testing Requirements
- Unit tests for all new functionality
- Integration tests for API-dependent features
- Mock external dependencies (httpx, API calls)
- Test edge cases and error conditions

### Tool Development
- Use `@tool` decorator from `ai/tools/base.py`
- Include comprehensive docstrings for schema generation
- Test security implications for code execution tools
- Follow existing patterns in `ai/tools/builtins.py`