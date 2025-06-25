# AI Library - Unified AI Interface

A professional, unified command-line interface for interacting with multiple AI providers including OpenRouter, OpenAI, Anthropic, and Google, with optional local model support via Ollama.

## Features

- **🎯 Simple CLI**: Just `ai "your question"` - works instantly
- **🌐 Multi-Provider**: Supports OpenRouter, OpenAI, Anthropic, Google APIs
- **🤖 Local Support**: Optional Ollama integration for local models
- **⚡ Fast Setup**: One-command installation with automatic configuration
- **🔧 Robust**: Built-in error handling, retries, and fallbacks
- **🧹 Clean Output**: Minimal logging for production use
- **📊 Status Monitoring**: Backend health checks and model listing

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

### Usage

```bash
# Basic usage
ai "What is Python?"

# Check system status
ai backend-status

# List available models
ai models-list
```

## Command Reference

### Basic Commands

```bash
# Ask questions
ai "Your question here"

# Stream responses (real-time output)
ai "Tell me a story" --stream

# Specify model
ai "Code question" --model openrouter/anthropic/claude-3-sonnet

# Use local backend (requires Ollama)
ai "Question" --backend local --model llama2

# Verbose output with metadata
ai "Question" --verbose
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
# Backend selection
ai "Question" --backend cloud      # Force cloud backend
ai "Question" --backend local      # Force local backend (Ollama)

# Model specification
ai "Question" --model gpt-4
ai "Question" --model openrouter/google/gemini-flash-1.5
ai "Question" --model anthropic/claude-3-haiku

# Response formatting
ai "Question" --stream             # Stream response tokens
ai "Question" --verbose            # Show timing and metadata
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
│   └── exceptions.py      # Custom exceptions
├── ai_wrapper.py          # CLI entry point wrapper
├── setup.sh               # Installation script
├── pyproject.toml         # Package configuration
└── tests/                 # Test suite
```

### Architecture

**Core Components:**
- **API Layer** (`ai/api.py`): Main interface with `ask()` function
- **Backend System**: Pluggable backends for different AI providers
- **CLI Interface**: Professional command-line tool with rich features
- **Session Management**: Support for persistent chat sessions
- **Error Handling**: Comprehensive exception hierarchy

**Design Principles:**
- **Unified Interface**: Single API for all providers
- **Provider Abstraction**: Backend-agnostic usage
- **Graceful Degradation**: Fallbacks when providers fail
- **Professional Output**: Clean, parseable responses
- **Configuration Flexibility**: Environment variables, config files

### Running Tests

**Unit Tests (Mocked - No API calls):**
```bash
# Run all unit tests (recommended for development)
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_cloud_backend.py
python -m pytest tests/test_local_backend.py
python -m pytest tests/test_cli_commands.py

# Run with coverage
python -m pytest tests/ --cov=ai --cov-report=html
```

**Integration Tests (Real API calls - Costs money):**
```bash
# Set API keys first
export OPENROUTER_API_KEY="your-key-here"
# or OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.

# Run integration tests (use sparingly)
./run_integration_tests.sh

# Or run specific integration test categories
python -m pytest tests/test_integration.py::TestRealAPIIntegration -m integration
python -m pytest tests/test_integration.py::TestProviderSpecificIntegration -m integration
```

**Test Types:**
- **Unit Tests**: Fast, mocked, no API costs - use for development
- **Integration Tests**: Real API calls, small costs (~$0.01-0.10) - use for validation
- **Ollama Tests**: Skipped unless Ollama is installed and running

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

- `APIKeyError`: Missing or invalid API key
- `ModelNotFoundError`: Specified model not available
- `BackendNotAvailableError`: Backend service unreachable
- `RateLimitError`: API rate limit exceeded

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