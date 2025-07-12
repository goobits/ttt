# AI Library - Unified AI Interface

A professional, unified command-line interface for interacting with multiple AI providers including OpenRouter, OpenAI, Anthropic, and Google, with optional local model support via Ollama.

## Features

- **🎯 Simple CLI**: Just `ai "your question"` - works instantly
- **🔧 Function Calling**: AI can call your Python functions and tools
- **🌐 Multi-Provider**: Supports OpenRouter, OpenAI, Anthropic, Google APIs
- **🤖 Local Support**: Optional Ollama integration for local models
- **⚡ Fast Setup**: One-command installation with automatic configuration
- **🛡️ Robust Error Handling**: Comprehensive error messages with helpful suggestions
- **🧹 Clean Output**: Minimal logging for production use
- **📊 Status Monitoring**: Backend health checks and model listing
- **⚡ Streaming Support**: Real-time response streaming
- **🎨 Rich Terminal UI**: Beautiful formatted output with color support

## Quick Start

### Installation

```bash
./setup.sh install
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Set up shell integration
- Create global `ai` command
- Generate environment template

### Configuration

Edit `.env` file with your API keys:

```bash
# OpenRouter (recommended - supports multiple models)
OPENROUTER_API_KEY=your-openrouter-key-here

# Direct provider keys (optional)
# OPENAI_API_KEY=your-openai-key-here
# ANTHROPIC_API_KEY=your-anthropic-key-here
# GOOGLE_API_KEY=your-google-key-here
```

## Migration from Other AI Tools

**Migrating from `llm` or similar tools?** The AI library provides drop-in compatibility with enhanced features:

```bash
# If you used: llm "question"
ai "question"                    # Same simple interface

# Enhanced with new features:
ai "question" --offline          # Force local models (Ollama)
ai "question" --online           # Force cloud models  
ai "question" --code             # Coding-optimized responses
ai "question" --verbose          # Show detailed metadata

# Flexible flag positioning (all equivalent):
ai "write a function" --code
ai --code "write a function"  
ai "write" --code "a function"

# Interactive mode (coming soon):
# ai --chat                      # Start persistent conversation
```

### Usage Examples

```bash
# Basic usage - just like llm
ai "What is Python?"

# Coding assistance with optimization
ai "write a Python function to sort a list" --code --verbose

# Force specific backend
ai "private question" --offline          # Uses local Ollama models
ai "complex analysis" --online --model gpt-4

# Stream responses in real-time
ai "Tell me a story" --stream

# System status and discovery
ai backend-status                        # Check what's configured
ai models-list                          # See available models

# Read from stdin (pipe support)
cat script.py | ai "review this code" --code
echo "2 + 2" | ai "what is this?" -
```

### Tools and Function Calling

The AI library includes a comprehensive set of built-in tools that are ready to use, plus the ability to create custom tools.

#### Built-in Tools

```python
from ai import ask
from ai.tools.builtins import web_search, read_file, calculate, get_current_time

# Use built-in tools directly
response = ask(
    "Search for the latest Python release and calculate 2^10",
    tools=[web_search, calculate]
)

# All built-in tools are automatically registered
response = ask(
    "What time is it in Tokyo?",
    tools=["get_current_time"]  # Can use tool names
)
```

**Available Built-in Tools:**

- **web_search**: Search the web for information
- **read_file**: Read contents of a file  
- **write_file**: Write content to a file
- **list_directory**: List files in a directory
- **run_python**: Execute Python code safely
- **get_current_time**: Get current time in any timezone
- **http_request**: Make HTTP API requests
- **calculate**: Perform mathematical calculations

#### Using Built-in Tools

```python
from ai import ask
from ai.tools import list_tools

# List all available tools
all_tools = list_tools()
print(f"Available tools: {[t.name for t in all_tools]}")

# List tools by category
web_tools = list_tools(category="web")
file_tools = list_tools(category="file")

# Use multiple built-in tools
response = ask(
    "Read the config.json file and tell me what port the server uses",
    tools=["read_file"]
)

# Complex multi-tool example
response = ask(
    "Search for Python asyncio tutorials, save the top 3 results to tutorials.txt",
    tools=["web_search", "write_file"]
)
```

#### Creating Custom Tools

```python
# Define custom tools using the @tool decorator
from ai.tools import tool

@tool
def get_weather(city: str, units: str = "fahrenheit") -> str:
    """Get weather information for a city.
    
    Args:
        city: Name of the city
        units: Temperature units (fahrenheit or celsius)
    """
    return f"Weather in {city}: 72°{units[0].upper()}, sunny"

@tool(category="database", description="Query user database")
def get_user(user_id: int) -> dict:
    """Get user information by ID.
    
    Args:
        user_id: The user's ID number
    """
    # Simulated database query
    return {
        "id": user_id,
        "name": "John Doe",
        "email": "john@example.com"
    }

# Use custom tools with built-in tools
response = ask(
    "What's the weather in NYC and what time is it there?",
    tools=[get_weather, "get_current_time"]
)

# Check tool usage
if response.tools_called:
    print("Tools were called:")
    for call in response.tool_calls:
        if call.succeeded:
            print(f"  {call.name}: {call.result}")
        else:
            print(f"  {call.name}: Error - {call.error}")
```

#### Tool Examples

```python
# File operations
response = ask(
    "List all Python files in the current directory",
    tools=["list_directory"]
)

# Web and calculation
response = ask(
    "Search for the speed of light and calculate how long it takes to reach Mars",
    tools=["web_search", "calculate"]
)

# Code execution
response = ask(
    "Write and run a Python script that generates the Fibonacci sequence",
    tools=["run_python"]
)

# API requests
response = ask(
    "Get the current Bitcoin price from the CoinGecko API",
    tools=["http_request"]
)

# Time zones
response = ask(
    "What time is it in Tokyo, London, and New York?",
    tools=["get_current_time"]
)
```

## Command Reference

### Basic Commands

```bash
# Simple usage (like llm)
ai "Your question here"

# NEW: Enhanced backend control
ai "Question" --offline                  # Force local models (Ollama)
ai "Question" --online                   # Force cloud models
ai "Question" --code                     # Coding-optimized responses
ai "Question" --verbose                  # Show detailed metadata

# Stream responses (real-time output)
ai "Tell me a story" --stream

# Specify model
ai "Code question" --model openrouter/anthropic/claude-3-sonnet

# Legacy backend specification (still supported)
ai "Question" --backend local --model llama2

# System prompts
ai "Translate this" --system "You are a translator"

# Temperature control
ai "Write a poem" --temperature 0.9

# Token limits
ai "Summarize this" --max-tokens 100

# Read from stdin (enhanced pipe support)
echo "What is this?" | ai -
cat file.txt | ai "Explain this code" -
cat script.py | ai "review this code" --code

# Use tools from CLI
ai "What time is it in Tokyo?" --tools get_current_time
ai "Search for Python tutorials" --tools web_search
ai "List files in current directory" --tools list_directory

# Multiple tools
ai "Search web and save results" --tools web_search,write_file

# Custom tools (module:function format)
ai "Process data" --tools my_module:process_data
ai "Analyze file" --tools /path/to/tools.py:analyze

# Built-in tools by category
ai "Read config.json" --tools read_file
ai "Calculate 15% of 250" --tools calculate

# NEW: Flexible flag positioning (all equivalent)
ai "write a function" --code --verbose
ai --code "write a function" --verbose  
ai --verbose --code "write a function"
```

### System Commands

```bash
# Check backend status and connectivity
ai backend-status

# List all available models
ai models-list

# Show help
ai --help
```

### Advanced Options

```bash
# NEW: Simple backend selection  
ai "Question" --offline            # Force local backend (Ollama)
ai "Question" --online             # Force cloud backend
ai "Question" --code               # Coding-optimized responses

# Legacy backend selection (still supported)
ai "Question" --backend cloud      # Force cloud backend
ai "Question" --backend local      # Force local backend (Ollama)

# Model specification
ai "Question" --model gpt-4
ai "Question" --model openrouter/google/gemini-flash-1.5
ai "Question" --model anthropic/claude-3-haiku

# Response formatting
ai "Question" --stream             # Stream response tokens
ai "Question" --verbose            # Show timing and metadata

# Model parameters
ai "Question" --temperature 0.7    # Creativity (0.0-2.0)
ai "Question" --max-tokens 500     # Response length limit
ai "Question" --system "You are..." # System prompt

# Short flags
ai "Question" -m gpt-4            # Model
ai "Question" -s "System prompt"   # System
ai "Question" -v                   # Verbose

# NEW: Smart features
ai "debug this function" --code    # Auto-detects coding context
ai "debug this function"           # Also works (auto-detection)
ai "Question" --verbose --online   # Combine multiple flags
```

## Backend Configuration

### Cloud Backend (Default)

The cloud backend uses LiteLLM to provide unified access to multiple AI providers:

**Supported Providers:**
- **OpenRouter** (recommended): Access to 100+ models through single API key
- **OpenAI**: GPT-3.5, GPT-4, and newer models
- **Anthropic**: Claude models
- **Google**: Gemini models

**Default Models:**
- Primary: `gpt-3.5-turbo`
- OpenRouter default: `google/gemini-flash-1.5`

### Local Backend (Optional)

The local backend uses Ollama for privacy-focused local inference:

```bash
# Install Ollama first
curl https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama2
ollama pull codellama
ollama pull mistral

# Use local models
ai "Question" --backend local --model llama2
```

**Configuration:**
```bash
# Optional: Custom Ollama URL
OLLAMA_BASE_URL=http://localhost:11434
```

## Python Library Usage

The AI library provides both synchronous and asynchronous APIs for integration into your Python applications.

### Synchronous API (Recommended for most use cases)

```python
from ai import ask, stream, chat

# Simple question
response = ask("What is Python?")
print(response)

# With model selection
response = ask("Explain async/await", model="gpt-4")
print(f"Response: {response}")
print(f"Model used: {response.model}")
print(f"Time taken: {response.time}s")

# Streaming responses
for chunk in stream("Tell me a story"):
    print(chunk, end="", flush=True)

# Chat sessions
with chat(system="You are a helpful coding assistant") as session:
    response1 = session.ask("What is a decorator?")
    response2 = session.ask("Show me an example")
    print(f"Conversation history: {len(session.history)} messages")
```

### Asynchronous API (For performance-critical applications)

For applications that need to handle many concurrent requests or integrate with async frameworks like FastAPI, use the async API:

```python
import asyncio
from ai import ask_async, stream_async, achat

async def main():
    # Async ask - non-blocking
    response = await ask_async("What is Python?")
    print(response)
    
    # Async streaming
    async for chunk in stream_async("Tell me a story"):
        print(chunk, end="", flush=True)
    
    # Async chat sessions
    async with achat(system="You are helpful") as session:
        response = session.ask("Hello")  # Session.ask() works in async context
        print(response)

# Run async code
asyncio.run(main())
```

### When to use Async vs Sync

**Use Synchronous API when:**
- Building simple scripts or CLI tools
- Working with synchronous code
- Processing requests one at a time
- Just getting started with the library

**Use Asynchronous API when:**
- Building web applications (FastAPI, aiohttp)
- Processing multiple requests concurrently
- Integration with async frameworks
- Performance is critical (can handle 10x+ more concurrent requests)

### Library Features

All features work with both sync and async APIs:

```python
from ai import ask, chat
from ai.tools.builtins import web_search, calculate

# Function calling with built-in tools
response = ask(
    "Search for Python 3.12 release date and calculate days since release",
    tools=[web_search, calculate]
)

# Custom tools
from ai.tools import tool

@tool
def get_user_data(user_id: int) -> dict:
    """Get user data from database."""
    return {"id": user_id, "name": "John Doe"}

response = ask("Get user 123's information", tools=[get_user_data])

# Persistent chat with save/load
from ai.chat import PersistentChatSession

session = PersistentChatSession()
session.ask("Remember: my name is Alice")
session.save("alice_session.json")

# Later...
session = PersistentChatSession.load("alice_session.json")
response = session.ask("What's my name?")  # Will remember "Alice"
```

## API Keys Setup

### OpenRouter (Recommended)

OpenRouter provides access to 100+ models through a single API key:

1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Get your API key from the dashboard
3. Add to `.env`: `OPENROUTER_API_KEY=sk-or-v1-...`

### Direct Provider Keys

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google
GOOGLE_API_KEY=AI...
```

## Development

### Project Structure

```
agents/
├── ai/                     # Core library package
│   ├── __init__.py        # Public API exports
│   ├── api.py             # Main API interface
│   ├── chat.py            # Chat session management
│   ├── cli.py             # Command-line interface
│   ├── backends/          # Backend implementations
│   │   ├── cloud.py       # Cloud provider backend
│   │   └── local.py       # Local Ollama backend
│   ├── tools/             # Function calling system
│   │   ├── __init__.py    # Tool decorator and exports
│   │   ├── base.py        # Core tool classes
│   │   ├── registry.py    # Tool registration system
│   │   └── execution.py   # Tool execution engine
│   └── exceptions.py      # Custom exceptions
├── ai_wrapper.py          # CLI entry point wrapper
├── setup.sh               # Installation script
├── pyproject.toml         # Package configuration
└── tests/                 # Test suite
```

### Architecture

**Core Components:**
- **API Layer** (`ai/api.py`): Main interface with `ask()` and `stream()` functions
- **Tool System** (`ai/tools/`): Function calling with automatic schema generation
- **Backend System**: Pluggable backends for different AI providers
- **CLI Interface**: Clean, simple argument parsing with rich output formatting
- **Session Management**: Support for persistent chat sessions (upcoming)
- **Error Handling**: User-friendly error messages with actionable suggestions

**Design Principles:**
- **Unified Interface**: Single API for all providers
- **Provider Abstraction**: Backend-agnostic usage
- **Function Calling**: Type-safe tool integration with automatic schema generation
- **Graceful Degradation**: Fallbacks when providers fail
- **Professional Output**: Clean, parseable responses
- **Configuration Flexibility**: Environment variables, config files

### Running Tests

**Unified Test Runner:**
```bash
# Run unit tests (default - free, fast)
./test.sh

# Run unit tests with coverage
./test.sh unit --coverage

# Run specific test file
./test.sh --test test_api

# Run integration tests (costs money, requires API keys)
./test.sh integration

# Run all tests (unit first, then integration)
./test.sh all

# Skip slow tests
./test.sh --markers "not slow"

# Verbose output
./test.sh unit --verbose

# Show help
./test.sh --help
```

**Test Types:**
- **Unit Tests**: Fast, mocked, no API costs - use for development
- **Integration Tests**: Real API calls, small costs (~$0.01-0.10) - use for validation
- **Combined**: Run unit tests first, then integration tests if unit tests pass

**API Key Setup for Integration Tests:**
```bash
# Set one or more API keys
export OPENROUTER_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"

# Then run integration tests
./test.sh integration
```

### Development Setup

```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 ai/ tests/
black ai/ tests/
```

## Troubleshooting

### Common Issues

**Command not found:**
```bash
# Restart terminal or source bashrc
source ~/.bashrc

# Check if binary exists
ls -la ~/.local/bin/ai
```

**API Key errors:**
```bash
# Check configuration
ai backend-status

# Verify .env file
cat .env
```

**Local backend issues:**
```bash
# Check Ollama status
ollama list

# Test Ollama directly
curl http://localhost:11434/api/tags
```

### Error Codes

- `APIKeyError`: Missing or invalid API key - shows which env var to set
- `ModelNotFoundError`: Specified model not available - suggests using models-list
- `BackendNotAvailableError`: Backend service unreachable - suggests checking backend-status
- `RateLimitError`: API rate limit exceeded - shows retry time
- `EmptyResponseError`: Model returned empty response - suggests rephrasing

## Security

- API keys are stored in local `.env` files (not tracked in git)
- Local backend option for sensitive queries
- No data logging or telemetry
- Secure HTTP connections for all API calls

## Performance

**Response Times:**
- OpenRouter: ~1-3 seconds
- Direct APIs: ~0.5-2 seconds  
- Local models: ~2-10 seconds (depends on hardware)

**Optimization:**
- Connection pooling for faster subsequent requests
- Async architecture for non-blocking operations
- Efficient token usage tracking

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Documentation**: This README covers all features
- **Issues**: Report bugs or request features via GitHub issues
- **Setup Problems**: Use `ai backend-status` for diagnostics

---

**Professional AI interface for developers who need reliability.**