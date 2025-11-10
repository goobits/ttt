# Glossary

Quick reference for key concepts and terminology used throughout TTT documentation.

## Core Concepts

### Backend
An abstraction layer that connects TTT to AI providers. TTT includes:
- **CloudBackend**: For cloud providers (OpenAI, Anthropic, Google, etc.) via LiteLLM
- **LocalBackend**: For local models via Ollama
- **Custom backends**: User-defined backends implementing `BaseBackend`

Example: When you use `model="gpt-4"`, TTT routes your request through CloudBackend.

### Provider
The actual AI service that generates responses (OpenAI, Anthropic, Google, Ollama). Backends connect to providers.

### Router
The system component that automatically selects the appropriate backend based on the model name and configuration. Handles fallbacks and intelligent routing.

### Model
An AI language model. Examples: `gpt-4`, `claude-3-opus`, `llama2`. TTT supports 100+ models across multiple providers.

### Response
The result of an AI request, wrapped in an `AIResponse` object containing:
- Generated text
- Metadata (model used, tokens, timing)
- Tool calls (if function calling was used)

### Session
A conversation context that maintains message history. Two types:
- **ChatSession**: In-memory conversation tracking
- **PersistentChatSession**: Save/load conversations to disk

### Tool
A Python function that AI models can call to perform actions. Also called "function calling".

Example:
```python
@tool
def get_weather(city: str) -> str:
    return f"Weather in {city}"
```

### Hook
A callback function in `app_hooks.py` that implements CLI command business logic. The CLI framework calls hooks when commands are executed.

### Plugin
An extension that adds functionality to TTT (custom backends, tools, or models). Loaded dynamically at runtime.

## Technical Terms

### Streaming
Receiving AI responses incrementally as they're generated, rather than waiting for the complete response. Uses `stream()` or `stream_async()`.

### Token
The basic unit of text processing for AI models. Roughly 4 characters = 1 token. Models have token limits (context window).

### Context Window
The maximum number of tokens a model can process in a single request (prompt + response).

### Temperature
A parameter (0.0-2.0) controlling response randomness:
- Low (0.0-0.3): More focused, deterministic
- Medium (0.5-0.8): Balanced creativity
- High (0.9-2.0): More creative, varied

### Top-p (Nucleus Sampling)
Alternative to temperature. Controls response diversity by sampling from the smallest set of tokens whose cumulative probability exceeds p.

### Model Registry
Central database of model metadata (capabilities, context length, pricing). Used for routing and validation.

## Configuration Terms

### Configuration Hierarchy
The order in which configuration sources are applied:
1. Programmatic (direct parameters)
2. Environment variables
3. Config files (`.ai.yaml`, etc.)
4. Default values

### API Key
Authentication credential for cloud AI providers. Set via environment variables or config files.
- OpenAI: `OPENAI_API_KEY`
- Anthropic: `ANTHROPIC_API_KEY`
- Google: `GOOGLE_API_KEY`

### Config File
YAML file containing TTT settings. Search locations:
- `./ai.yaml` (project-specific)
- `./.ai.yaml` (hidden project file)
- `~/.config/ttt/config.yaml` (user config)
- `~/.ai.yaml` (hidden user file)

## Development Terms

### LiteLLM
Third-party library providing unified interface to 100+ AI providers. Used by CloudBackend.

### Ollama
Local AI model server. Allows running open-source models privately without cloud APIs.

### Goobits
CLI framework used to generate TTT's command-line interface from `goobits.yaml`.

### Auto-generated File
A file created by tools (like `cli.py` from goobits). Never edit directly - changes will be overwritten.

### Rate Limiting
Restriction on API request frequency. Varies by provider and plan. TTT includes smart rate limiting in tests.

### Mock/Mocking
Test technique using fake responses instead of real API calls. Faster and free for testing.

## Common Patterns

### Sync vs Async
- **Synchronous**: Blocks until operation completes (`ask()`, `stream()`)
- **Asynchronous**: Non-blocking, allows concurrent operations (`ask_async()`, `stream_async()`)

### Function Calling
AI capability where models can request tool execution to perform actions (web search, calculations, API calls).

### Prompt Engineering
Crafting effective prompts to get desired AI responses. Includes system prompts, few-shot examples, and formatting.

### Fallback
Automatic switching to alternative backend/model when primary option fails.

---

**Related**: See [Index](./INDEX.md) for navigation to detailed documentation on these concepts.
