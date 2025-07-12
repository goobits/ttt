# Testing Foundation for AI Library

This document outlines the testing foundation and patterns established for the AI library.

## Test Structure

The testing suite is built on pytest with the following key components:

### 1. **Core Tool Testing** (`test_builtin_tools.py`)
- **Calculate Tool**: Comprehensive tests covering valid expressions, edge cases (division by zero), invalid inputs, and security (blocking unsafe operations)
- **File Operations**: Tests for read/write operations with error handling
- **Web Search**: Mocked HTTP requests and error handling
- **Code Execution**: Python code execution with timeout and error handling

### 2. **Backend Testing** (`test_local_backend.py`)
- **LocalBackend**: Uses `pytest-mock`'s `mocker` fixture to patch `httpx.AsyncClient`
- **Mocked Responses**: Simulates Ollama API responses for ask/stream operations
- **Error Handling**: Tests HTTP errors, connection failures, and model not found scenarios
- **Async Testing**: Proper async/await patterns with `@pytest.mark.asyncio`

### 3. **CLI Testing** (`test_modern_cli.py`)
- **Typer CliRunner**: Uses Typer's built-in testing utilities for reliable CLI testing
- **Command Testing**: Tests all CLI commands (ask, chat, backend-status, etc.)
- **Argument Parsing**: Verifies proper parsing of flags and options
- **Help Output**: Tests help text generation and error handling

## Key Testing Patterns

### Tool Testing Pattern
```python
def test_calculate_edge_cases(self):
    """Test edge cases and error conditions."""
    # Division by zero
    result = calculate("1 / 0")
    assert "Error: Division by zero" in result
    
    # Invalid syntax
    result = calculate("2 +")
    assert "Error" in result
    
    # Security: unsafe operations should be blocked
    result = calculate("__import__('os')")
    assert "Error" in result
```

### Backend Testing Pattern
```python
@pytest.mark.asyncio
async def test_ask_success_mocked(self, backend):
    """Test successful ask request with mocked httpx.AsyncClient."""
    with patch("httpx.AsyncClient") as mock_client_class:
        # Set up mock response
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Hello!"}
        
        # Configure async context manager
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        
        # Test the backend
        response = await backend.ask("Hello, AI!")
        assert str(response) == "Hello!"
```

### CLI Testing Pattern
```python
def test_ask_command_basic(self):
    """Test basic ask command functionality."""
    runner = CliRunner()
    with patch('ai.cli._handle_query') as mock_handle:
        result = runner.invoke(app, ["ask", "What is Python?"])
        
        assert result.exit_code == 0
        args = mock_handle.call_args[0][0]
        assert args["prompt"] == "What is Python?"
```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_builtin_tools.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=ai --cov-report=html
```

### Test Categories
```bash
# Run only unit tests
pytest tests/ -m unit

# Run only integration tests  
pytest tests/ -m integration

# Skip slow tests
pytest tests/ -m "not slow"

# Run real API tests (requires API keys)
pytest tests/ -m real_api
```

### Specific Test Patterns
```bash
# Run calculate tool tests
pytest tests/test_builtin_tools.py::TestCalculate -v

# Run LocalBackend tests
pytest tests/test_local_backend.py::TestLocalBackend -v

# Run CLI tests
pytest tests/test_modern_cli.py::TestTyperCLI -v
```

## Dependencies

### Required Dependencies
- `pytest = "^7.0.0"` (already in pyproject.toml)
- `pytest-asyncio = "^0.21.0"` (already in pyproject.toml)
- `pytest-cov = "^4.0.0"` (already in pyproject.toml)

### Recommended Addition
Add to `pyproject.toml` under `[tool.poetry.group.dev.dependencies]`:
```toml
pytest-mock = "^3.11.0"
```

## Test Markers

Current markers defined in `pyproject.toml`:
```toml
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests", 
    "benchmark: marks tests as performance benchmarks",
    "examples: marks tests as usage examples",
    "real_api: marks tests that make real API calls",
    "asyncio: marks tests as async tests",
]
```

## Foundation Examples

See `test_foundation_example.py` for comprehensive examples of:
1. **Tool Testing**: Calculate tool with edge cases and security testing
2. **Backend Testing**: LocalBackend with properly mocked httpx client
3. **CLI Testing**: Typer CLI with CliRunner and argument validation
4. **Async Testing**: Proper async/await patterns with mocking

## Key Principles

1. **Comprehensive Edge Cases**: Test valid inputs, invalid inputs, edge cases, and error conditions
2. **Proper Mocking**: Use `unittest.mock` and `pytest-mock` to isolate units under test
3. **CLI Testing**: Use Typer's CliRunner for reliable CLI testing instead of subprocess
4. **Async Patterns**: Use `@pytest.mark.asyncio` and `AsyncMock` for async testing
5. **Security Testing**: Ensure unsafe operations are properly blocked
6. **Error Handling**: Test all error paths and exception scenarios

This foundation provides a robust starting point for maintaining and expanding the test suite as the AI library evolves.