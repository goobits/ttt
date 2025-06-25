# AI - The Unified AI Library

A single, elegant interface for local and cloud AI models. Write once, run anywhere.

## ✨ Features

- **🎯 Simple API**: Just `ask("your question")` - it really is that simple
- **🤖 Universal**: Works with local models (Ollama) and cloud APIs (OpenAI, Anthropic, Google)
- **🧠 Smart Routing**: Automatically picks the best model for your query
- **💬 Chat Sessions**: Context managers for multi-turn conversations
- **⚡ Streaming**: Real-time token-by-token responses
- **🔧 Configurable**: YAML config files, environment variables, or programmatic setup
- **🛡️ Robust**: Built-in fallbacks, retries, and error handling
- **🔌 Extensible**: Plugin system for custom backends
- **📝 Model Registry**: Define custom models and aliases

## 🚀 Quick Start

```bash
pip install ai
```

```python
from ai import ask

# Just ask - it works out of the box
response = ask("What is quantum computing?")
print(response)
```

That's it! The library will automatically:
- Detect available backends (local Ollama or cloud APIs)
- Select the best model for your query
- Handle all the complexity behind the scenes

## 📖 Examples

### Basic Usage

```python
from ai import ask, stream, chat

# Simple questions
answer = ask("What's the capital of France?")
print(answer)  # "Paris"

# Get rich metadata
response = ask("Explain machine learning")
print(f"Model: {response.model}")
print(f"Time: {response.time:.2f}s")
print(f"Tokens: {response.tokens_out}")
```

### Preferences

```python
# Prefer speed over quality
quick_answer = ask("Quick fact about Python", fast=True)

# Prefer quality over speed  
detailed_answer = ask("Comprehensive analysis of climate change", quality=True)

# Specify backend
local_answer = ask("Private question", backend="local")
cloud_answer = ask("Complex reasoning", backend="cloud")
```

### Streaming Responses

```python
from ai import stream

# Real-time streaming
for chunk in stream("Write a short story about a robot"):
    print(chunk, end="", flush=True)
```

### Conversations

```python
from ai import chat

# Multi-turn conversations with context
with chat() as session:
    session.ask("I'm learning Python")
    session.ask("What are decorators?")  # Knows you're learning Python
    response = session.ask("Show me an example")  # Continues the context

# Persistent conversations that can be saved
with chat(persist=True) as session:
    session.ask("Remember this: My favorite color is blue")
    session.ask("I'm working on a web scraping project")
    session.save("my_assistant.json")

# Resume conversations later
from ai import PersistentChatSession
session = PersistentChatSession.load("my_assistant.json")
response = session.ask("What's my favorite color?")  # Will remember it's blue
```

### System Prompts

```python
# Set the AI's behavior
with chat(system="You are a helpful coding assistant") as assistant:
    code = assistant.ask("Write a function to reverse a string")
    review = assistant.ask("Review this code for bugs", code=my_code)
```

### Multi-Modal (Vision)

```python
from ai import ask, ImageInput

# Analyze a single image
response = ask([
    "What's in this image?",
    ImageInput("photo.jpg")
], model="gpt-4-vision-preview")

# Compare multiple images
response = ask([
    "What are the differences between these images?",
    ImageInput("before.png"),
    ImageInput("after.png")
])

# Image from URL
response = ask([
    "Describe this chart:",
    ImageInput("https://example.com/chart.png")
])

# Stream responses with images
for chunk in stream([
    "Write a detailed analysis of this artwork:",
    ImageInput("painting.jpg")
]):
    print(chunk, end="")
```

## 🔧 Configuration

### Environment Variables

```bash
# For cloud models
export OPENAI_API_KEY=your-key
export ANTHROPIC_API_KEY=your-key  
export GOOGLE_API_KEY=your-key

# For local models (optional)
export OLLAMA_BASE_URL=http://localhost:11434
```

### Configuration File

Create `~/.config/ai/config.yaml` (see [examples/config/ai.yaml](examples/config/ai.yaml) for full example):

```yaml
default_backend: auto
default_model: gpt-3.5-turbo
timeout: 30
enable_fallbacks: true
fallback_order:
  - cloud
  - local

model_aliases:
  fast: gpt-3.5-turbo
  best: gpt-4
  coding: claude-3-sonnet-20240229
  local: llama2

# Define custom models
models:
  - name: gpt-4-turbo
    provider: openai
    provider_name: gpt-4-turbo-preview
    aliases: [turbo, preview]
    speed: medium
    quality: high
    capabilities: [text, reasoning, code]

# Backend-specific configuration
backends:
  local:
    default_model: llama2
    base_url: http://localhost:11434
  cloud:
    default_model: gpt-3.5-turbo
    provider_order: [openai, anthropic, google]

# Smart routing keywords
routing:
  code_keywords: [code, function, debug, python]
  speed_keywords: [quick, fast, simple]
  quality_keywords: [analyze, explain, comprehensive]
```

### Programmatic Configuration

```python
from ai import configure

configure(
    openai_api_key="your-key",
    default_backend="cloud",
    timeout=60
)
```

## 🤖 Model Support

### Cloud Models

**OpenAI**
- `gpt-4` - Best reasoning and complex tasks
- `gpt-3.5-turbo` - Fast and efficient for most tasks
- `gpt-4-vision-preview` - Vision capabilities for image analysis

**Anthropic**  
- `claude-3-opus-20240229` - Top-tier reasoning with vision support
- `claude-3-sonnet-20240229` - Great for coding
- `claude-3-haiku-20240307` - Fast and efficient

**Google**
- `gemini-pro` - Strong general performance
- `gemini-pro-vision` - Multimodal capabilities
- `gemini-1.5-pro` - Extended context window
- `gemini-1.5-pro-vision` - Vision with extended context

### Local Models (via Ollama)

Install Ollama, then pull models:

```bash
ollama pull llama2        # General purpose
ollama pull codellama     # Code-focused
ollama pull mistral       # Efficient and capable
```

## 🎯 Smart Routing

The library automatically selects the best model based on your query:

```python
# Automatically detects this is a coding question
# and uses a code-optimized model
ask("Debug this Python function")

# Detects this needs fast response
# and uses a quick model  
ask("What's 2+2?")

# Detects complex reasoning needed
# and uses a high-quality model
ask("Analyze the socioeconomic implications of AI")
```

Override anytime:

```python
ask("Any question", model="gpt-4")        # Specific model
ask("Any question", fast=True)            # Prefer speed
ask("Any question", quality=True)         # Prefer quality
ask("Any question", backend="local")      # Force local
```

## 🛠️ Command Line Interface

### Basic Usage

```bash
# Basic usage
ai "What is Python?"

# Streaming mode
ai "Tell me a story" --stream

# Specify model
ai "Code review this" --model claude-3-sonnet

# Use system prompt
ai "Explain this" --system "You are a teacher"

# Verbose output with metadata
ai "Hello" --verbose
```

### Model Management

```bash
# List all available models
ai models list

# Show only local models
ai models list --local

# Show only cloud models  
ai models list --cloud

# Show detailed model information
ai models list --verbose

# Pull a model for local use (Ollama)
ai models pull llama2

# Pull with progress details
ai models pull codellama --verbose
```

### Backend Management

```bash
# Check status of all backends
ai backend status

# Show detailed backend information
ai backend status --verbose
```

The backend status command will:
- Test connectivity to local Ollama instance
- Verify API keys for cloud providers (OpenAI, Anthropic, Google)
- Show which backends are ready to use
- Provide helpful configuration tips

## 🧪 Advanced Usage

### Persistent Chat Sessions

Save and resume conversations across program runs:

```python
from ai import chat, PersistentChatSession

# Create a persistent session
with chat(persist=True, session_id="project_assistant") as session:
    session.ask("I'm building a web app with FastAPI")
    session.ask("It needs user authentication")
    
    # Save the conversation
    session.save("project_chat.json")
    
    # Get session summary
    summary = session.get_summary()
    print(f"Tokens used: {summary['total_tokens_in']}")
    print(f"Cost: ${summary['total_cost']:.4f}")

# Load and continue later
session = PersistentChatSession.load("project_chat.json")
response = session.ask("What auth library should I use?")

# Export conversation
print(session.export_messages(format="markdown"))

# Track costs and usage
print(f"Total cost: ${session.metadata['total_cost']:.4f}")
for model, usage in session.metadata['model_usage'].items():
    print(f"{model}: {usage['count']} calls, ${usage['cost']:.4f}")
```

### Async Support

```python
import asyncio
from ai import ask_async, stream_async, achat

async def main():
    # Async requests
    response = await ask_async("What's Python?")
    
    # Async streaming
    async for chunk in stream_async("Tell me a story"):
        print(chunk, end="")
    
    # Async chat
    async with achat() as session:
        response = await session.ask("Hello!")

asyncio.run(main())
```

### Custom Backends and Plugins

The AI library supports custom backends through a powerful plugin system:

```python
from ai import register_backend, load_plugin
from ai.backends import BaseBackend
from pathlib import Path

# Method 1: Register a backend class directly
class MyCustomBackend(BaseBackend):
    @property
    def name(self):
        return "custom"
    
    # Implement required methods
    async def ask(self, prompt, **kwargs):
        # Your implementation
        pass

register_backend("custom", MyCustomBackend)

# Method 2: Load a plugin from file
load_plugin(Path("path/to/plugin.py"))

# Method 3: Auto-discovery - place plugins in:
# ~/.config/ai/plugins/
# ~/.ai/plugins/
# ./ai_plugins/

# Use your custom backend
response = ask("Hello", backend="custom")
```

See [examples/plugins/](examples/plugins/) for complete plugin examples, including:
- **Echo Backend**: Simple example that echoes prompts
- **Mock LLM Backend**: Generates realistic mock responses for testing

### Model Registry

Define and manage custom models:

```python
from ai import model_registry
from ai.models import ModelInfo

# Add a custom model definition
model_registry.add_model(ModelInfo(
    name="my-fine-tuned-model",
    provider="openai",
    provider_name="ft:gpt-3.5-turbo:my-org:custom:abc123",
    aliases=["my-model", "custom"],
    speed="fast",
    quality="high",
    capabilities=["text", "domain-specific"],
    context_length=4096
))

# Use via name or alias
response = ask("Domain-specific question", model="my-model")

# List all registered models
models = model_registry.list_models()
aliases = model_registry.list_aliases()
```

### Advanced Configuration

The configuration system supports:
- **YAML configuration files** with full schema
- **Model definitions** in config files
- **Backend-specific settings**
- **Smart routing customization**
- **Plugin paths and loading**

See [examples/config/ai.yaml](examples/config/ai.yaml) for a complete configuration example.

## 📚 API Reference

### Core Functions

- `ask(prompt, **kwargs) -> AIResponse` - Ask a question
- `stream(prompt, **kwargs) -> Iterator[str]` - Stream response  
- `chat(**kwargs) -> ChatSession` - Create chat session

### Parameters

- `model: str` - Specific model to use
- `system: str` - System prompt
- `backend: str | Backend` - Backend selection
- `temperature: float` - Sampling temperature (0-1)
- `max_tokens: int` - Maximum tokens to generate
- `fast: bool` - Prefer speed over quality
- `quality: bool` - Prefer quality over speed

### AIResponse

The response object behaves like a string but includes metadata:

```python
response = ask("Hello")

# Use as string
print(response)           # The response text
print(len(response))      # Length of response
print(response.upper())   # String methods work

# Access metadata  
print(response.model)     # Model that generated it
print(response.backend)   # Backend used
print(response.time)      # Time taken (seconds)
print(response.tokens_in) # Input tokens
print(response.tokens_out)# Output tokens
print(response.cost)      # Estimated cost (if available)

# Check status
if response.failed:
    print(f"Error: {response.error}")
```

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🚨 Error Handling

The library provides a comprehensive exception hierarchy for robust error handling:

### Exception Hierarchy

```python
from ai import AIError  # Base exception for all library errors

try:
    response = ask("Hello", model="gpt-4")
except AIError as e:
    # Catches any error from the library
    print(f"Error: {e}")
    print(f"Details: {e.details}")
```

### Common Exceptions

```python
from ai import (
    BackendNotAvailableError,  # Backend not found or misconfigured
    ModelNotFoundError,        # Model doesn't exist
    APIKeyError,              # Missing or invalid API key
    RateLimitError,           # API rate limit exceeded
    MultiModalError,          # Multi-modal input not supported
    SessionLoadError,         # Failed to load saved session
)

# Specific error handling
try:
    response = ask("Question", model="gpt-5")
except ModelNotFoundError as e:
    print(f"Model {e.details['model']} not found")
    print("Try: gpt-4, gpt-3.5-turbo, claude-3-sonnet")
except APIKeyError as e:
    print(f"Please set {e.details['env_var']}")
except RateLimitError as e:
    retry_after = e.details.get('retry_after', 60)
    print(f"Rate limited. Retry after {retry_after}s")
```

See [examples/exception_handling.py](examples/exception_handling.py) for comprehensive examples.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built for developers who want AI that just works.**