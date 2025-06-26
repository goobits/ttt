# Tool System Phase 2: Chat + CLI Integration

This document describes the implementation of Tool System Phase 2, which adds tool support to chat sessions and the CLI.

## Overview

Phase 2 integrates the tool system with chat sessions and the command-line interface, enabling:
- Tools to be specified when creating chat sessions
- Tool usage to be tracked in chat history
- Tool persistence when saving/loading sessions
- CLI support for specifying tools via command-line flags

## Implementation Details

### 1. Chat Session Tool Support

#### ChatSession Class Updates (ai/api.py)
- Added `tools` parameter to `__init__` method
- Updated `ask()` and `stream()` methods to pass tools to backend
- Tools are passed through to the backend for each request

#### PersistentChatSession Class Updates (ai/chat.py)
- Added `tools` parameter to `__init__` method
- Added `tools_used` tracking to metadata
- Updated `ask()` method to:
  - Pass tools to backend
  - Track tool calls in response history
  - Update tool usage statistics in metadata
- Updated `stream()` method to pass tools to backend
- Added tool serialization/deserialization methods:
  - `_serialize_tools()`: Converts tools to JSON-serializable format
  - `_deserialize_tools()`: Restores tools from saved format
- Updated `save()` and `load()` methods to persist tools

### 2. Tool Persistence

Tools are serialized in three formats:
1. **function_name**: Regular Python functions with name and module
2. **tool_definition**: ToolDefinition objects with name and description
3. **tool_name**: Simple string references to registry tools

When loading a session, tools are restored as string references that can be:
- Resolved from the global tool registry
- Re-imported from modules
- Passed as-is to backends that accept tool names

### 3. CLI Integration

#### CLI Updates (ai/cli.py)
- Added `--tools` flag to accept comma-separated tool specifications
- Added `resolve_tools()` function to handle tool resolution from:
  - Registry names: `"tool_name"`
  - Module imports: `"module:function"`
  - File imports: `"/path/to/file.py:function"`
- Updated help text with tool examples
- Added tool information to verbose output

#### Tool Specification Format
```bash
# Single tool from registry
ai "Question" --tools "get_weather"

# Multiple tools from module
ai "Question" --tools "math:sqrt,math:pow"

# Mix of sources
ai "Question" --tools "registered_tool,mymodule:func,/scripts/tools.py:custom"
```

### 4. Context Manager Support

The `chat()` context manager now supports tools:
```python
with chat(tools=[func1, func2]) as session:
    response = session.ask("Use the tools")
```

Both regular and persistent sessions support tools through the context manager.

## Usage Examples

### Basic Chat with Tools
```python
from ai import chat

def get_weather(city: str) -> str:
    return f"Weather in {city}: 72°F, sunny"

with chat(tools=[get_weather]) as session:
    response = session.ask("What's the weather in NYC?")
    print(response)
```

### Persistent Session with Tools
```python
from ai.chat import PersistentChatSession

session = PersistentChatSession(tools=[get_weather])
response = session.ask("Check weather in London")

# Save session (tools are preserved)
session.save("weather_session.json")

# Load session (tools restored as references)
loaded = PersistentChatSession.load("weather_session.json")
```

### CLI Usage
```bash
# Using a registered tool
ai "What's the weather?" --tools "get_weather"

# Using module functions
ai "Calculate sqrt of 16" --tools "math:sqrt"

# Multiple tools
ai "Complex task" --tools "tool1,module:tool2"

# Verbose mode shows tool calls
ai "Use tools" --tools "math:sqrt" --verbose
```

## Testing

Comprehensive tests have been added in `tests/test_chat_tools.py`:
- ChatSession tool support tests
- PersistentChatSession tool tracking tests
- Tool serialization/deserialization tests
- CLI tool resolution tests
- Context manager tests

All tests pass successfully.

## Future Enhancements

1. **Tool Discovery**: Auto-discover tools from installed packages
2. **Tool Validation**: Validate tool signatures before passing to backends
3. **Tool Documentation**: Generate help for available tools
4. **Tool Caching**: Cache resolved tools for better performance
5. **Tool Versioning**: Handle tool version changes in saved sessions

## Backward Compatibility

The implementation maintains full backward compatibility:
- Sessions without tools work as before
- Existing saved sessions can be loaded without issues
- The tools parameter is optional in all APIs