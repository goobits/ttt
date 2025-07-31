# Development Guide

This guide covers development setup, testing, code style, and contributing to the TTT library.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pipx (for isolated installation)
- git

### Installation

For development work, always use the editable installation:

```bash
# Clone the repository
git clone https://github.com/goobits/ttt.git
cd ttt

# Install in development mode (RECOMMENDED)
./setup.sh install --dev

# This creates an editable installation where code changes 
# are immediately reflected without needing to reinstall
```

The setup script automatically handles:
- Python extras installation (`local` extra for httpx)
- System package installation (git, pipx, curl) via apt-get
- No manual dependency installation required

### Alternative Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev,local]"
```

## Testing

### Test Structure

The test suite uses pytest with comprehensive coverage:

- **Unit Tests**: Fast, mocked, no external dependencies
- **Integration Tests**: Real API calls, requires API keys
- **Marked Tests**: `unit`, `integration`, `slow`, `asyncio`

### Running Tests

**Always use the test script for proper rate limiting:**

```bash
# Run unit tests (default - free, fast)
./test.sh

# Run unit tests with coverage
./test.sh unit --coverage

# Run specific test file
./test.sh --test test_api

# Run integration tests (costs money, requires API keys)
export OPENROUTER_API_KEY=your-key-here
./test.sh integration          # Will prompt for confirmation
./test.sh integration --force  # Skip confirmation

# Run all tests (unit first, then integration)
./test.sh all

# Skip slow tests
./test.sh --markers "not slow"

# Verbose output
./test.sh unit --verbose
```

### Direct pytest Usage

For unit tests only:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_cli_modern.py -v

# Run with markers
pytest tests/ -m "not integration"  # Skip integration tests
pytest tests/ -m "not slow"         # Skip slow tests

# Run with coverage
pytest tests/ --cov=ttt --cov-report=html
```

### Writing Tests

Follow these patterns:

```python
# Unit test with mocking
@pytest.mark.unit
def test_ask_with_mock(mock_backend):
    response = ask("Hello", backend=mock_backend)
    assert response.succeeded
    mock_backend.ask.assert_called_once()

# Integration test with rate limiting
@pytest.mark.integration
def test_real_api(delayed_ask):
    response = delayed_ask("What is 2+2?")
    assert "4" in str(response)

# Async test
@pytest.mark.asyncio
async def test_async_stream():
    chunks = []
    async for chunk in stream_async("Count to 3"):
        chunks.append(chunk)
    assert len(chunks) > 0
```

## Code Style

### Formatting and Linting

The project uses strict code quality standards:

```bash
# Format code with Black
black src/ttt/ tests/

# Run linter
ruff src/ttt/ tests/

# Type checking
mypy src/ttt/

# Run all checks
black src/ttt/ tests/ && ruff src/ttt/ tests/ && mypy src/ttt/
```

### Style Configuration

- **Black**: Line length 88
- **Ruff**: Checks E, W, F, I, B, C4, UP; Ignores E501, B008, C901
- **MyPy**: Strict mode enabled

### Code Guidelines

1. **Follow existing patterns** - Look at similar files for style
2. **Type hints required** - All functions must have type annotations
3. **Docstrings required** - All public functions need docstrings
4. **No commented code** - Remove, don't comment out
5. **Descriptive names** - Clear variable and function names

## Project Structure

```
ttt/
├── src/ttt/               # Main package
│   ├── __init__.py       # Public API exports
│   ├── __main__.py       # CLI entry point
│   ├── api.py            # Core API functions
│   ├── cli.py            # CLI implementation
│   ├── backends/         # Backend implementations
│   │   ├── base.py       # Abstract base class
│   │   ├── cloud.py      # Cloud provider backend
│   │   └── local.py      # Local Ollama backend
│   ├── tools/            # Function calling system
│   │   ├── base.py       # Tool decorators
│   │   ├── builtins.py   # Built-in tools
│   │   └── registry.py   # Tool registration
│   ├── config.py         # Configuration management
│   └── exceptions.py     # Custom exceptions
├── tests/                # Test suite
├── examples/             # Usage examples
├── docs/                 # Documentation
├── setup.sh             # Installation script
├── test.sh              # Test runner script
└── pyproject.toml       # Package configuration
```

## Development Workflow

### 1. Making Changes

```bash
# Create a feature branch
git checkout -b feature/my-feature

# Make your changes
# ... edit files ...

# Run tests
./test.sh

# Format and lint
black src/ttt/ tests/
ruff src/ttt/ tests/
mypy src/ttt/

# Commit changes
git add .
git commit -m "Add my feature"
```

### 2. Testing Changes

```bash
# Test CLI directly (dev mode reflects changes immediately)
ttt "test prompt"
ttt status
ttt models

# Run unit tests
./test.sh

# Test specific functionality
pytest tests/test_my_feature.py -v
```

### 3. Documentation

Update documentation for any new features:

- API changes → `docs/api-reference.md`
- Configuration → `docs/configuration.md`
- Examples → `examples/` directory
- Architecture → `docs/architecture.md`

## Adding New Features

### Adding a New Backend

1. Create backend class in `src/ttt/backends/`:

```python
from ttt.backends import BaseBackend
from ttt.models import AIResponse

class MyBackend(BaseBackend):
    @property
    def name(self) -> str:
        return "my-backend"

    @property
    def is_available(self) -> bool:
        # Check if backend can be used
        return True

    async def ask(self, prompt: str, **kwargs) -> AIResponse:
        # Implement completion
        pass

    async def astream(self, prompt: str, **kwargs):
        # Implement streaming
        pass

    async def models(self) -> List[str]:
        # Return available models
        pass

    async def status(self) -> Dict[str, Any]:
        # Return status info
        pass
```

2. Register the backend (in plugin or config)
3. Add tests in `tests/test_backends_my.py`

### Adding a New Tool

1. Add to `src/ttt/tools/builtins.py` or create new file:

```python
from ttt.tools import tool

@tool
def my_tool(param1: str, param2: int = 10) -> str:
    """Tool description for schema generation.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    """
    # Implementation
    return f"Result: {param1}, {param2}"
```

2. The tool is automatically registered
3. Add tests in `tests/test_tools_builtin.py`

### Adding CLI Commands

1. Add command in `src/ttt/cli.py`:

```python
@main.command()
@click.argument("query")
@click.option("--model", "-m", help="Model to use")
def mycommand(query, model):
    """Description of command."""
    # Implementation using app_hooks
    from ttt.app_hooks import on_mycommand
    on_mycommand(query, model)
```

2. Implement hook in `src/ttt/app_hooks.py`
3. Add tests in `tests/test_cli_modern.py`

## Debugging

### Debug Mode

```bash
# Enable debug logging
export AI_LOG_LEVEL=DEBUG

# Run with verbose output
ttt ask "test" --verbose

# Debug specific component
python -m ttt.backends.cloud
```

### Common Issues

**Import Errors**
```bash
# Ensure dev installation
./setup.sh install --dev

# Or reinstall
pip install -e ".[dev,local]"
```

**Test Failures**
```bash
# Run specific test with output
pytest tests/test_file.py::test_name -v -s

# Check test coverage
./test.sh unit --coverage
```

## Contributing

### Before Submitting

1. **Run all tests**: `./test.sh`
2. **Format code**: `black src/ttt/ tests/`
3. **Check linting**: `ruff src/ttt/ tests/`
4. **Type check**: `mypy src/ttt/`
5. **Update docs**: Document new features
6. **Add tests**: Cover new functionality

### Pull Request Guidelines

1. Create focused PRs - one feature per PR
2. Write clear commit messages
3. Update relevant documentation
4. Ensure all tests pass
5. Add tests for new features
6. Follow existing code patterns

### Commit Message Format

```
type: subject

body (optional)

footer (optional)
```

Types: feat, fix, docs, style, refactor, test, chore

Example:
```
feat: add vision support for GPT-4

- Add image parameter to ask() function
- Update CloudBackend to handle images
- Add tests for multimodal inputs

Closes #123
```

## Performance Considerations

1. **Connection Pooling**: Reuse HTTP connections
2. **Async Operations**: Use async/await properly
3. **Caching**: Cache model lists and static data
4. **Lazy Loading**: Import heavy dependencies only when needed
5. **Resource Cleanup**: Properly close connections and files

## Security Guidelines

1. **Never log API keys** - Use masked output
2. **Validate inputs** - Especially for code execution
3. **Sanitize paths** - For file operations
4. **Limit scopes** - For tool permissions
5. **Review dependencies** - Keep them minimal and updated

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite: `./test.sh all`
4. Create git tag: `git tag v1.0.0`
5. Push to GitHub: `git push origin main --tags`
6. GitHub Actions handles PyPI release

## Getting Help

- Check existing tests for examples
- Review similar implementations in the codebase
- See `docs/` for detailed documentation
- Open an issue for questions or bugs