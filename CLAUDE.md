# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Information

**Package**: `goobits-ttt` | **Command**: `ttt` | **Python**: 3.8+

A professional CLI and Python library for interacting with multiple AI providers (OpenRouter, OpenAI, Anthropic, Google, Ollama).

## Essential Commands

```bash
./setup.sh install --dev         # Development setup (required)
./test.sh                       # Run unit tests (fast, no API calls)
./test.sh --test test_cli_smoke # Smoke tests (under 1 second)
./test.sh integration --force   # Integration tests (requires API keys)
ruff format src/ttt/ tests/     # Format code
ruff check src/ttt/ tests/      # Lint code
mypy src/ttt/                   # Type check
pytest tests/path/to/test.py::test_name -v  # Run single test
```

## Architecture Overview

**Request Flow**: User → CLI/API → Router → Backend → Provider → Response

### Key Components

1. **API** (`src/ttt/api.py`): Core functions `ask()`, `stream()`, `chat()` with async variants
2. **Backends** (`src/ttt/backends/`): 
   - `CloudBackend`: LiteLLM integration for cloud providers
   - `LocalBackend`: Ollama integration for local models
   - Selected automatically by model name patterns
3. **Router** (`src/ttt/routing.py`): Manages backend selection and fallbacks
4. **Tools** (`src/ttt/tools/`): `@tool` decorator enables function calling
5. **Config** (`src/ttt/config/`): Hierarchical configuration (defaults → file → env → runtime)
6. **CLI** (`src/ttt/cli.py`): Click-based commands that call hooks in `cli_handlers.py`

### Critical Patterns

- **Async handling**: Uses background event loop via `async_utils.py`
- **Test mocking**: CLI tests need `@pytest.mark.integration` decorator
- **Tool development**: Tools require comprehensive docstrings for schema generation
- **Integration tests**: Automatically mocked via `conftest.py`, bypass with `--real-api`
- **Configuration**: Uses `ConfigManager` singleton pattern

### Testing Notes

- Unit tests use mocked responses by default (no API costs)
- Integration tests mock HTTP calls via `tests/utils/http_mocks.py`
- Always use `./test.sh` for integration tests (includes rate limiting)

## Further Reading

- **Architecture details**: `docs/architecture.md`
- **Testing guide**: `tests/README.md` 
- **Development setup**: `docs/development.md`
- **Configuration**: `docs/configuration.md`
- **Code style settings**: `pyproject.toml`
