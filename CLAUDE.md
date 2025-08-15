# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Information

**Package**: `goobits-ttt` (PyPI) | **Command**: `ttt` | **Version**: 1.0.3 | **Python**: 3.8+

A professional CLI and Python library for interacting with multiple AI providers (OpenRouter, OpenAI, Anthropic, Google, Ollama).

## Key Development Commands

### Quick Reference
- `./setup.sh install --dev` - Development installation with editable mode (REQUIRED for development)
- `./test.sh` - Run unit tests (40s, no API calls)
- `./test.sh --test test_cli_smoke` - Fast smoke tests (0.45s)
- `./test.sh integration --force` - Run integration tests (requires API keys, costs ~$0.01-0.10)
- `ruff format src/ttt/ tests/` - Format code (line length: 120)
- `ruff check src/ttt/ tests/` - Lint code
- `mypy src/ttt/` - Type checking
- `pytest tests/test_specific.py::TestClass::test_method -v` - Run single test

### Test Execution Notes
- **pipx installation**: Tests use `~/.local/share/pipx/venvs/goobits-ttt/bin/pytest`
- **Integration tests**: 61 tests marked with `@pytest.mark.integration` use HTTP mocking by default
- **Real API testing**: Use `pytest --real-api` or `REAL_API_TESTS=1 pytest` to bypass mocks
- **Current status**: 100% tests passing (443/443)

## High-Level Architecture

### Core Flow: CLI → API → Backend → Provider

```
User Input (CLI/Python) → Core API (ask/stream/chat) → Router → Backend → Provider → Response
```

### Key Components

1. **API Layer** (`src/ttt/api.py`)
   - Provides `ask()`, `stream()`, `chat()` with async variants
   - Returns `AIResponse` objects with metadata
   - Handles sync/async conversion via `async_utils.py`

2. **Backend System** (`src/ttt/backends/`)
   - `BaseBackend`: Abstract interface all backends implement
   - `CloudBackend`: LiteLLM integration for cloud providers
   - `LocalBackend`: Ollama integration for local models
   - Backends selected automatically by model name patterns

3. **Routing** (`src/ttt/routing.py`)
   - `Router` class manages backend selection
   - Model registry with metadata and capabilities
   - Automatic fallback between providers

4. **Tool System** (`src/ttt/tools/`)
   - `@tool` decorator for function calling
   - Built-in tools: web_search, calculate, file operations
   - Tool executor with safety constraints
   - Tools passed to AI via standardized schema

5. **Configuration** (`src/ttt/config/`)
   - Hierarchical: defaults → file → env → runtime
   - Per-backend configuration sections
   - Model aliases (@fast → gpt-3.5-turbo)

6. **CLI** (`src/ttt/cli.py`)
   - Click-based with rich formatting
   - Hook system: commands call `cli_handlers.py`
   - Parameter conversion for API compatibility

### Testing Infrastructure

- **HTTP Mocking**: `conftest.py` auto-mocks integration tests via `smart_integration_mocking`
- **Mock Responses**: `tests/utils/http_mocks.py` provides context-aware responses
- **Rate Limiting**: Built-in delays when using real APIs to avoid 429 errors

### Code Style
- Black formatting (line length: 120, not 88 as incorrectly stated before)
- Ruff linting with specific ignores (E501, B008, C901)
- Type hints encouraged but not enforced (`disallow_untyped_defs = false`)

### Important Patterns
- Async code uses background event loop (`async_utils.py`)
- All CLI tests need `@pytest.mark.integration` to enable mocking
- Tools must have comprehensive docstrings for schema generation
- Configuration uses `ConfigManager` singleton pattern

## Documentation References

- **README.md** - Quick start and examples
- **docs/architecture.md** - Detailed system design
- **tests/README.md** - Testing guide with performance metrics
- **docs/development.md** - Contributing guidelines
