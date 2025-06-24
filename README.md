# Agents.py - AI that just works

Dead simple AI agent library for Python. No boilerplate, just results.

```python
from agents import ai

response = ai("Explain quantum computing")
print(response)
```

## Installation

```bash
pip install agents-py
```

## Quick Start

### One-line AI queries
```python
from agents import ai

# Just ask
answer = ai("What's the capital of France?")
print(answer)  # "Paris"

# With context
solution = ai("Fix this code:", code=broken_code)

# Get metadata
response = ai("Explain AI")
print(f"Model: {response.model}, Time: {response.time}s")
```

### Conversations
```python
from agents import chat

with chat() as assistant:
    assistant("I need help with Python")
    assistant("How do I read a CSV file?")
    solution = assistant("Show me an example")
```

### Streaming
```python
from agents import stream

for chunk in stream("Tell me a story"):
    print(chunk, end="", flush=True)
```

## Features

- **Zero friction**: Just `ai("your question")`
- **Smart routing**: Automatically picks the best model for your query
- **Easy conversations**: Context managers for multi-turn chats  
- **Rich responses**: Get both text and metadata (time, model, tokens)
- **Streaming support**: Real-time responses for long content
- **Pythonic API**: Works how you'd expect Python to work

## Model Selection

Agents.py automatically routes your queries to the best model:

- **Math queries** → Fast, accurate models
- **Code questions** → Code-optimized models
- **Creative writing** → Creative models
- **Quick facts** → Fast, efficient models

Override anytime:
```python
ai("Hello", model="gpt-4")  # Use specific model
ai("Hello", fast=True)      # Prefer speed
ai("Hello", quality=True)   # Prefer quality
```

## Setup

Set your API keys:
```bash
export OPENAI_API_KEY=your-key
export ANTHROPIC_API_KEY=your-key
export GOOGLE_API_KEY=your-key
```

Or use `.env`:
```
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
GOOGLE_API_KEY=your-key
```

## More Examples

### Smart Model Routing
```python
# Math queries automatically use fast, accurate models
response = ai("Calculate 15% tip on $42.50")
print(f"Response: {response}")
print(f"Model used: {response.model}")  # Auto-selected for math

# Code queries use code-optimized models
code = '''
def factorial(n):
    return 1 if n <= 1 else n * factorial(n-1)
'''
response = ai("What does this code do?", code=code)
print(f"Model used: {response.model}")  # Auto-selected for code
```

### Conversations with System Prompts
```python
with chat(system="You are a helpful Python tutor") as tutor:
    tutor("I'm new to Python")
    response = tutor("What are lists?")
    print(response)
    
    response = tutor("Show me an example")
    print(response)
```

### Error Handling
```python
response = ai("Complex query")
if response.failed:
    print(f"Error: {response.error}")
else:
    print(f"Success: {response}")
    print(f"Time taken: {response.time:.2f}s")
```

### Using Specific Models
```python
# Use a specific model
response = ai("Hello!", model="gpt-4o-mini")

# Prefer speed over quality
response = ai("Quick question", fast=True)

# Prefer quality over speed
response = ai("Complex analysis", quality=True)
```

## Advanced Usage

### Custom Configuration
```python
from agents import ModelConfiguration, ModelInfo

# Create custom configuration
config = ModelConfiguration()
config.add_model(ModelInfo(
    name="my-model",
    provider="openai",
    provider_name="gpt-4-turbo",
    aliases=["custom"],
    speed="fast",
    quality="high"
))

# Use with custom router
from agents import ModelRouter, ChatSession
router = ModelRouter(config)
session = ChatSession(config=config)
```

### Async Support
```python
import asyncio
from agents import ai_async, stream_async, achat

async def main():
    # Async one-liner
    response = await ai_async("What's Python?")
    print(response)
    
    # Async streaming
    async for chunk in stream_async("Tell me a story"):
        print(chunk, end="")
    
    # Async chat
    async with achat() as assistant:
        response = await assistant("Hello!")
        print(response)

asyncio.run(main())
```

### OpenRouter Support
```python
# If you have an OpenRouter API key, additional models are available
response = ai("Hello", model="openrouter/gemini-flash-1.5")
response = ai("Hello", model="openrouter/gpt-4")
response = ai("Hello", model="openrouter/claude-3-sonnet")
```

## Requirements

- Python 3.8+
- `litellm` for API access
- API keys for your chosen providers

## License

MIT