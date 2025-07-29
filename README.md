# 🤖 Goobits TTT

Professional, unified command-line interface and Python library for interacting with multiple AI providers including OpenRouter, OpenAI, Anthropic, and Google, with optional local model support via Ollama.

## 🔗 Related Projects

- **[Matilda](https://github.com/goobits/matilda)** - AI assistant
- **[Goobits STT](https://github.com/goobits/stt)** - Speech-to-Text engine
- **[Goobits TTS](https://github.com/goobits/tts)** - Text-to-Speech engine
- **[Goobits TTT](https://github.com/goobits/ttt)** - Text-to-Text processing (this project)

## 📋 Table of Contents

- [Architecture](#️-architecture)
- [Quick Start](#-quick-start)
- [Command Reference](#-command-reference)
- [Function Calling & Tools](#-function-calling--tools)
- [Python Library Usage](#-python-library-usage)
- [Backend Configuration](#-backend-configuration)
- [Configuration Management](#️-configuration-management)
- [Tech Stack](#️-tech-stack)

## 🏗️ Architecture

Goobits TTT implements a **CLI → Backend → Provider** abstraction pattern where a unified interface coordinates multiple AI providers through pluggable backend systems:

```
CLI Interface / Python API
         ↓
    ┌─────────────────────────────────────┐
    │  Backend Abstraction Layer          │
    │  • Cloud provider routing          │
    │  • Local model support (Ollama)    │
    │  • Error handling and retries      │
    │  • Response streaming              │
    └─────────────┬───────────────────────┘
                  ▼ Routes to providers
    ┌─────────────────────────────────────┐
    │  AI Providers (Multi-Provider)      │
    │  • OpenRouter (100+ models)        │
    │  • OpenAI, Anthropic, Google       │
    │  • Function calling capabilities   │
    │  • Local Ollama integration        │
    └─────────────────────────────────────┘
```

## ✨ Key Features

- **🎯 Simple CLI** - Just `ttt "your question"` - works instantly
- **🔧 Function Calling** - AI can call your Python functions and tools
- **🌐 Multi-Provider** - OpenRouter, OpenAI, Anthropic, Google APIs
- **🤖 Local Support** - Optional Ollama integration for privacy
- **⚡ Fast Setup** - One-command installation with automatic configuration
- **🛡️ Robust Error Handling** - Comprehensive error messages with helpful suggestions
- **📊 Status Monitoring** - Backend health checks and model listing
- **🎨 Rich Terminal UI** - Beautiful formatted output with color support
- **🔄 Direct Pipe Support** - `echo "text" | ttt` - no dash needed!
- **📋 Smart Help** - `ttt` shows help, `ttt "question"` executes

## 🚀 Quick Start

```bash
# Install in one command
./setup.sh install        # For end users (from PyPI)
./setup.sh install --dev  # For developers (local source)

# Restart terminal or reload shell
source ~/.bashrc

# Set up API key (choose one)
export OPENAI_API_KEY=sk-your-key-here
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
# Or add to your .env file

# Configure default model
ttt config set models.default gpt-4

# Create model aliases
ttt config set alias.work claude-3-opus

# Start using immediately
ttt "What is Python?"
ttt -m @work "Write a function to sort a list" --code

# Pipe text directly to AI
echo "Explain this code" | ttt
cat file.txt | ttt "Review this code"

# Use local models (privacy-focused)
ttt config set backends.default local
ttt config set models.default qwen2.5:32b
ttt "private question"

# Use built-in tools
ttt "What time is it in Tokyo?" --tools get_current_time
ttt "Search for Python tutorials" --tools web_search

# Interactive chat mode with persistence
ttt chat                           # Start new chat session
ttt chat --resume                  # Continue last session
ttt chat --list                    # Show all sessions
ttt chat --id SESSION_ID           # Resume specific session
```

## ⚙️ Configuration Management

### Quick Configuration

```bash
# View all settings
ttt config

# Set API keys (masked when displayed)
ttt config set openai_key sk-your-key-here
ttt config set anthropic_key sk-ant-your-key-here
ttt config set openrouter_key sk-or-v1-your-key-here

# Configure behavior
ttt config set models.default gpt-4         # Default model
ttt config set backends.default local       # Backend (local/cloud/auto)
ttt config set timeout 60                   # Request timeout
ttt config set retries 3                    # Max retry attempts
```

### Common Configurations

| Use Case | Configuration |
|----------|---------------|
| **Privacy-First** | `ttt config set backends.default local && ttt config set models.default qwen2.5:32b` |
| **Fast Responses** | `ttt config set models.default gpt-3.5-turbo` |
| **Coding Assistant** | `ttt config set models.default claude-3-sonnet && ttt config set backends.default cloud` |
| **Cost-Effective** | `ttt config set openrouter_key sk-or-... && ttt config set models.default google/gemini-flash` |

All settings saved to `~/.config/ttt/config.yaml`

## Migration from Other AI Tools

**Migrating from `llm` or similar tools?** The AI library provides drop-in compatibility with enhanced features:

```bash
# If you used: llm "question"
ttt "question"                    # Same simple interface

# Enhanced with new features:
ttt "question" --code             # Coding-optimized responses
ttt "question" --verbose          # Show detailed metadata

# Easy configuration management (NEW):
ttt config set models.default qwen2.5:32b     # Set default model for Qwen users
ttt config set backends.default local          # Set default to local for privacy
ttt config                        # View all current settings

# Flexible flag positioning (all equivalent):
ttt "write a function" --code
ttt --code "write a function"
ttt "write" --code "a function"

# Interactive chat mode with session management
ttt chat                           # Start new chat session
ttt chat --resume                  # Continue last session
ttt chat --list                    # Show all sessions
```

### Usage Examples

```bash
# Basic usage - just like llm
ttt "What is Python?"

# Show help menu
ttt

# Pipe text directly (NEW!)
echo "Hello world" | ttt
cat script.py | ttt "Review this code"
git diff | ttt "Explain these changes"

# Coding assistance with optimization
ttt "write a Python function to sort a list" --code --verbose

# Specify models directly
ttt "private question" --model qwen2.5:32b  # Uses local model automatically
ttt "complex analysis" --model gpt-4        # Uses cloud model automatically

# Stream responses in real-time
ttt "Tell me a story" --stream

# System status and discovery
ttt status                               # Check backend connectivity
ttt models                               # List available models
ttt config                               # View configuration

# Traditional stdin support (also works)
echo "2 + 2" | ttt -
```

### Tools and Function Calling

The AI library includes a comprehensive set of built-in tools that are ready to use, plus the ability to create custom tools.

#### Built-in Tools

```python
from ttt import ask
from ttt.tools.builtins import web_search, read_file, calculate, get_current_time

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
from ttt import ask
from ttt.tools import list_tools

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
from ttt.tools import tool

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
ttt "Your question here"

# Show help menu
ttt --help

# NEW: Direct pipe support (no dash needed!)
echo "Hello world" | ttt
cat file.txt | ttt
git diff | ttt

# Enhanced features
ttt "Question" --code                     # Coding-optimized responses
ttt "Question" --verbose                  # Show detailed metadata

# Stream responses (real-time output)
ttt "Tell me a story" --stream

# Specify model
ttt "Code question" --model openrouter/anthropic/claude-3-sonnet

# Local model specification (automatic routing)
ttt "Question" --model llama2

# System prompts
ttt "Translate this" --system "You are a translator"

# Temperature control
ttt "Write a poem" --temperature 0.9

# Token limits
ttt "Summarize this" --max-tokens 100

# Enhanced pipe support (multiple ways)
echo "What is this?" | ttt               # NEW: Direct pipe
echo "What is this?" | ttt               # Direct pipe
cat file.txt | ttt "Explain this code"   # Pipe with additional prompt
cat script.py | ttt "review this code" --code

# Use tools from CLI
ttt "What time is it in Tokyo?" --tools get_current_time
ttt "Search for Python tutorials" --tools web_search
ttt "List files in current directory" --tools list_directory

# Multiple tools
ttt "Search web and save results" --tools web_search,write_file

# Custom tools (module:function format)
ttt "Process data" --tools my_module:process_data
ttt "Analyze file" --tools /path/to/tools.py:analyze

# Built-in tools by category
ttt "Read config.json" --tools read_file
ttt "Calculate 15% of 250" --tools calculate

# Flexible flag positioning (all equivalent)
ttt "write a function" --code --verbose
ttt --code "write a function" --verbose
ttt --verbose --code "write a function"
```

### System Commands

```bash
# Check backend status and connectivity
ttt status

# List all available models
ttt models

# Configuration management
ttt config                               # Show all settings
ttt config get models.default            # Get specific value
ttt config set models.default gpt-4      # Set value
ttt config set alias.fast gpt-3.5-turbo  # Create alias
ttt config --reset                       # Reset to defaults

# Show help
ttt --help
```

### Interactive Chat Mode

```bash
# Start a new chat session with persistence
ttt chat

# Resume your last chat session
ttt chat --resume

# List all saved chat sessions
ttt chat --list

# Resume a specific session by ID
ttt chat --id 20241220_120530_abc123

# Chat with specific model or system prompt
ttt chat -m @claude -s "You are a coding expert"

# Chat commands:
# /exit or /quit - End the session
# /clear - Clear chat history
# /help - Show available commands
```

### Advanced Options

```bash
# Enhanced features
ttt "Question" --code               # Coding-optimized responses

# Model specification
ttt "Question" --model gpt-4
ttt "Question" --model gemini-flash-1.5
ttt "Question" --model anthropic/claude-3-haiku

# Model aliases with @ syntax
ttt -m @fast "Question"                  # Uses gpt-3.5-turbo
ttt -m @best "Question"                  # Uses gpt-4
ttt -m @coding "Question"                # Uses google/gemini-1.5-pro
ttt -m @claude "Question"                # Uses claude-3-sonnet

# Response formatting
ttt "Question" --stream             # Stream response tokens
ttt "Question" --verbose            # Show timing and metadata

# Model parameters
ttt "Question" --temperature 0.7    # Creativity (0.0-2.0)
ttt "Question" --max-tokens 500     # Response length limit
ttt "Question" --system "You are..." # System prompt

# Short flags
ttt "Question" -m gpt-4            # Model
ttt "Question" -s "System prompt"   # System
ttt "Question" -v                   # Verbose

# NEW: Smart features
ttt "debug this function" --code    # Auto-detects coding context
ttt "debug this function"           # Also works (auto-detection)
ttt "Question" --verbose --model gpt-4  # Combine multiple flags
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
- Primary: `gemini-flash-1.5`
- Model aliases: `fast` (gpt-3.5-turbo), `best` (gpt-4), `cheap` (gpt-3.5-turbo), `coding` (google/gemini-1.5-pro), `local` (llama2)

### Local Backend (Optional)

The local backend uses Ollama for privacy-focused local inference:

```bash
# Use local models (automatic routing)
ttt "Question" --model llama2
```

**Note**: Ollama and models will be automatically set up when needed through the setup.sh installation process.

**Configuration:**
```bash
# Optional: Custom Ollama URL
OLLAMA_BASE_URL=http://localhost:11434
```

## Python Library Usage

The AI library provides both synchronous and asynchronous APIs for integration into your Python applications.

### Synchronous API (Recommended for most use cases)

```python
from ttt import ask, stream, chat

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
from ttt import ask_async, stream_async, achat

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
from ttt import ask, chat
from ttt.tools.builtins import web_search, calculate

# Function calling with built-in tools
response = ask(
    "Search for Python 3.12 release date and calculate days since release",
    tools=[web_search, calculate]
)

# Custom tools
from ttt.tools import tool

@tool
def get_user_data(user_id: int) -> dict:
    """Get user data from database."""
    return {"id": user_id, "name": "John Doe"}

response = ask("Get user 123's information", tools=[get_user_data])

# Persistent chat with save/load
from ttt.chat import PersistentChatSession

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
3. Set environment variable: `export OPENROUTER_API_KEY=sk-or-v1-...`

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
.
├── ttt/                    # Core library package
│   ├── __init__.py        # Public API exports
│   ├── __main__.py        # CLI entry point
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
│   │   └── executor.py    # Tool execution engine
│   └── exceptions.py      # Custom exceptions
├── setup.sh               # Installation script
├── pyproject.toml         # Package configuration
└── tests/                 # Test suite
```

### Architecture

**Core Components:**
- **API Layer** (`ttt/api.py`): Main interface with `ask()` and `stream()` functions
- **Tool System** (`ttt/tools/`): Function calling with automatic schema generation
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
./setup.sh install --dev  # Recommended: uses pipx with editable install

# Run linting
ruff src/ttt/ tests/
black src/ttt/ tests/
mypy src/ttt/
```

## Troubleshooting

### Common Issues

**Command not found:**
```bash
# Restart terminal or source bashrc
source ~/.bashrc

# Check if binary exists
ls -la ~/.local/bin/ttt
```

**API Key errors:**
```bash
# Check configuration
ttt status

# Verify .env file
cat .env
```

**Local backend issues:**
```bash
# Check Ollama status
ollama list

# Test Ollama directly (if manually installed)
curl http://localhost:11434/api/tags
```

### Error Codes

- `APIKeyError`: Missing or invalid API key - shows which env var to set
- `ModelNotFoundError`: Specified model not available - suggests using 'ttt models'
- `BackendNotAvailableError`: Backend service unreachable - suggests checking 'ttt status'
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
- **Setup Problems**: Use `ttt status` for diagnostics

---

**Professional AI interface for developers who need reliability.**
