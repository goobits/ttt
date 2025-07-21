# Testing Guide for TTT Library

This document outlines the testing foundation and patterns for the TTT (Talk to Transformer) library.

## Test Structure

The testing suite is built on pytest with comprehensive coverage across all components:

### **Core Components**

#### 1. **API Testing** (`test_api_*.py`)
- **Core API** (`test_api_core.py`): Basic ask/stream/chat functionality
- **Streaming API** (`test_api_streaming.py`): Streaming responses and async operations
- **Response objects**: AIResponse, error handling, metadata validation

#### 2. **Backend Testing** (`test_backends_*.py`) 
- **Cloud Backend** (`test_backends_cloud.py`): LiteLLM integration, provider routing
- **Local Backend** (`test_backends_local.py`): Ollama integration with mocked HTTP calls
- **Error Handling**: Rate limits, authentication, model availability

#### 3. **CLI Testing** (`test_cli_modern.py`)
- **Click Framework**: Modern Click-based CLI with rich-click styling
- **Command Testing**: All commands (ask, chat, list, config, tools, status, models, info, export)
- **Hook System**: Integration with app_hooks.py for command execution
- **Help & Validation**: Help text, option parsing, error handling

#### 4. **Tool System** (`test_tools_*.py`)
- **Built-in Tools** (`test_tools_builtin.py`): calculate, web_search, code_execution, file operations
- **Custom Tools** (`test_tools_custom.py`): Tool registration and decoration patterns
- **Tool Integration** (`test_tools_chat.py`): Tool usage in chat sessions

#### 5. **Configuration & Routing**
- **Configuration** (`test_config_loading.py`): YAML loading, environment variables, hierarchy
- **Model Routing** (`test_routing.py`): Provider selection, model registry, fallbacks
- **Models** (`test_models.py`): Model definitions, capabilities, metadata

## Key Testing Patterns

### CLI Testing Pattern (New Click Interface)
```python
from click.testing import CliRunner
from ttt.cli import main

def test_ask_command():
    """Test the modern Click-based CLI."""
    runner = CliRunner()
    
    with patch("ttt.app_hooks.on_ask") as mock_hook:
        result = runner.invoke(main, ["ask", "What is Python?"])
        
        assert result.exit_code == 0
        mock_hook.assert_called_once()
```

### Backend Testing Pattern (Mocked HTTP)
```python
@pytest.mark.asyncio
async def test_local_backend():
    """Test LocalBackend with mocked httpx."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Hello!"}
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        
        backend = LocalBackend()
        response = await backend.ask("Hello, AI!")
        assert str(response) == "Hello!"
```

### Tool Testing Pattern (Security & Edge Cases)
```python
def test_calculate_tool_security():
    """Test that unsafe operations are blocked."""
    from ttt.tools.builtins import calculate
    
    # Valid operation
    result = calculate("2 + 2")
    assert "Result: 4" in result
    
    # Security: unsafe operations should be blocked
    result = calculate("__import__('os')")
    assert "Error" in result
    
    # Edge case: division by zero
    result = calculate("1 / 0")
    assert "Error: Division by zero" in result
```

### Hook System Testing
```python
@patch("ttt.app_hooks.on_chat")
def test_chat_command_integration(mock_hook):
    """Test CLI integration with hook system."""
    runner = CliRunner()
    mock_hook.return_value = None  # Avoid actual chat loop
    
    result = runner.invoke(main, [
        "chat", "--model", "gpt-4", "--session", "test"
    ])
    
    assert result.exit_code == 0
    mock_hook.assert_called_once()
```

## Running Tests

### **Using the Test Script (Recommended)**
```bash
# Run unit tests (fast, no API calls)
./test.sh unit

# Run integration tests (requires API keys, costs money)
./test.sh integration  

# Run all tests
./test.sh all

# Run with coverage
./test.sh unit --coverage

# Run specific test files
./test.sh --test test_cli_modern.py
```

### **Direct pytest Usage**
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

### **Test Categories**

Tests are marked with these pytest markers:

- `unit`: Fast tests with mocking, no external dependencies
- `integration`: Real API calls, requires API keys and costs money  
- `slow`: Time-intensive tests
- `asyncio`: Async test functions

## CLI Testing Details

### **Commands Tested**

The new Click CLI includes these commands, all tested in `test_cli_modern.py`:

- `ttt ask "question"` - Single question/answer
- `ttt chat` - Interactive chat session
- `ttt list models|sessions|tools` - List resources
- `ttt config get|set|list` - Configuration management
- `ttt tools enable|disable|list` - Tool management
- `ttt status` - Backend health check
- `ttt models` - List available models
- `ttt info MODEL` - Model details
- `ttt export SESSION` - Export chat history

### **Hook System**

Commands are implemented via hooks in `app_hooks.py`:
- `on_ask()` - Handles ask commands
- `on_chat()` - Handles interactive chat
- `on_list()` - Handles list commands
- `on_config_*()` - Configuration operations
- `on_tools_*()` - Tool management
- etc.

Tests mock these hooks to verify CLI integration without executing actual functionality.

## Integration Tests & Rate Limiting

See `README_RATE_LIMITING.md` for details on:
- API rate limit management
- Environment variable configuration  
- `delayed_ask`, `delayed_stream`, `delayed_chat` fixtures
- Cost awareness for integration tests

## Dependencies

### **Required (already in pyproject.toml)**
- `pytest ^7.0.0`
- `pytest-asyncio ^0.21.0` 
- `pytest-cov ^4.0.0`

### **CLI Testing**
- `click` - CLI framework
- `rich-click` - Enhanced Click with rich formatting

## Best Practices

### **1. Test Isolation**
- Use mocking to isolate units under test
- Patch external dependencies (HTTP, file system, etc.)
- Each test should be independent and repeatable

### **2. Comprehensive Edge Cases**
- Test valid inputs, invalid inputs, edge cases, error conditions
- Include security testing for code execution and file operations
- Test rate limiting, authentication failures, network errors

### **3. CLI Testing**
- Use Click's CliRunner for reliable CLI testing
- Mock app hooks to test CLI integration without side effects
- Test help text, option parsing, command validation

### **4. Async Testing** 
- Use `@pytest.mark.asyncio` for async test functions
- Use `AsyncMock` for async dependencies
- Proper async context manager mocking with `__aenter__`

### **5. Integration Testing**
- Mark with `@pytest.mark.integration`
- Use rate limiting fixtures (`delayed_ask`, etc.)  
- Require explicit API keys and cost acknowledgment

## File Organization

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── test_api_*.py              # API functionality tests  
├── test_backends_*.py         # Backend implementation tests
├── test_cli_modern.py         # Modern Click CLI tests
├── test_tools_*.py            # Tool system tests
├── test_config_loading.py     # Configuration tests
├── test_*_streaming.py        # Streaming functionality tests
├── test_integration.py        # Real API integration tests
└── README_*.md               # Testing documentation
```

## Examples

See individual test files for comprehensive examples:

- **CLI Testing**: `test_cli_modern.py` 
- **Backend Testing**: `test_backends_local.py`, `test_backends_cloud.py`
- **Tool Testing**: `test_tools_builtin.py`
- **Integration Testing**: `test_integration.py`

This testing foundation ensures robust coverage across all TTT components while maintaining fast unit tests and comprehensive integration testing.