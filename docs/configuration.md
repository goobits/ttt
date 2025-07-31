# Configuration Guide

The TTT library provides flexible configuration through multiple sources with clear precedence rules.

## Configuration Hierarchy

Configuration is loaded in this order (highest to lowest precedence):

1. **Programmatic configuration** via `configure()`
2. **Environment variables**
3. **Configuration files** (YAML)
4. **Default values**

## Configuration Files

The library searches for configuration files in these locations:

1. `./ttt.yaml` or `./ttt.yml` - Project-specific config
2. `./.ttt.yaml` or `./.ttt.yml` - Hidden project config
3. `~/.config/ttt/config.yaml` or `~/.config/ttt/config.yml` - User config
4. `~/.ttt.yaml` or `~/.ttt.yml` - Hidden user config
5. `config.yaml` - Default configuration (built-in)
6. `.env` - Environment variables and API keys

## Environment Variables

### API Keys
- `OPENROUTER_API_KEY` - Recommended (access to 100+ models)
- `OPENAI_API_KEY` - Direct OpenAI access
- `ANTHROPIC_API_KEY` - Direct Anthropic access
- `GOOGLE_API_KEY` - Direct Google access
- `OLLAMA_BASE_URL` - Local Ollama URL (default: http://localhost:11434)

### System Configuration
- `AI_CONFIG_FILE` - Path to configuration file
- `AI_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## CLI Configuration

### View Settings
```bash
# View all settings
ttt config

# Get specific value
ttt config get models.default
ttt config get models.aliases
```

### Set Configuration
```bash
# Set API keys (masked when displayed)
ttt config set openai_key sk-your-key-here
ttt config set anthropic_key sk-ant-your-key-here
ttt config set openrouter_key sk-or-v1-your-key-here

# Configure behavior
ttt config set models.default gpt-4         # Default model
ttt config set backends.default local       # Backend (local/cloud/auto)
ttt config set timeout 60                   # Request timeout
ttt config set retries 3                    # Max retry attempts

# Create model aliases
ttt config set alias.work claude-3-opus
```

### Reset Configuration
```bash
ttt config --reset  # Reset to defaults
```

## Common Configurations

| Use Case | Configuration |
|----------|---------------|
| **Privacy-First** | `ttt config set backends.default local && ttt config set models.default qwen2.5:32b` |
| **Fast Responses** | `ttt config set models.default gpt-3.5-turbo` |
| **Coding Assistant** | `ttt config set models.default claude-3-sonnet && ttt config set backends.default cloud` |
| **Cost-Effective** | `ttt config set openrouter_key sk-or-... && ttt config set models.default google/gemini-flash` |

## Configuration Schema

### Complete YAML Configuration Example

```yaml
# Basic settings
default_backend: auto  # auto, local, cloud, or custom backend name
default_model: null    # null for auto-selection or specific model
timeout: 30           # Request timeout in seconds
max_retries: 3        # Maximum retry attempts
enable_fallbacks: true # Enable automatic fallback to other backends

# Backend fallback order
fallback_order:
  - cloud
  - local

# Local backend settings
ollama_base_url: http://localhost:11434

# Model aliases for convenience
model_aliases:
  fast: gpt-3.5-turbo
  best: gpt-4
  cheap: gpt-3.5-turbo
  coding: google/gemini-1.5-pro
  local: llama2
  claude: claude-3-sonnet
  gpt4: gpt-4

# Custom model definitions
models:
  - name: my-custom-model
    provider: openai
    provider_name: ft:gpt-3.5-turbo:org:custom:id
    aliases: [custom, tuned]
    speed: fast
    quality: high
    capabilities: [text, domain-specific]
    context_length: 4096
    cost_per_token: 0.0001

# Backend-specific configuration
backends:
  local:
    default_model: llama2
    timeout: 60
  cloud:
    default_model: gpt-3.5-turbo
    provider_order: [openai, anthropic, google]

# Smart routing configuration
routing:
  code_keywords: [code, function, debug, algorithm, implement, syntax]
  speed_keywords: [quick, fast, simple, brief, tldr]
  quality_keywords: [analyze, explain, comprehensive, detailed, thorough]
  
  # Model selection rules
  rules:
    - if: {contains: [code, python]}
      prefer_model: claude-3-sonnet
    - if: {length_gt: 200}
      prefer_model: gpt-4
```

## Model Routing

### Automatic Model Selection

The library automatically selects appropriate models based on:

- **Cloud models**: Patterns like `openrouter/`, `gpt-`, `claude-`, `gemini-`
- **Local models**: Assumes Ollama for non-cloud patterns
- **Default model**: `openrouter/google/gemini-flash-1.5`
- **Model aliases**: `fast`, `best`, `cheap`, `coding`, `local` (defined in config.yaml)

### Using Model Aliases

```bash
# Use predefined aliases
ttt ask -m @fast "Quick question"
ttt ask -m @best "Complex analysis"
ttt ask -m @coding "Write a function"
ttt ask -m @claude "Explain this concept"
ttt ask -m @local "Private question"

# Create custom aliases
ttt config set alias.work claude-3-opus
ttt ask -m @work "Work-related task"
```

## Programmatic Configuration

### Python API

```python
from ttt import configure

# Update configuration at runtime
configure(
    default_backend="cloud",
    default_model="gpt-4",
    timeout=60,
    openai_api_key="your-key",
    # Any other configuration options
)

# Configure with custom settings
configure(
    openrouter_api_key="sk-or-...",
    default_backend="cloud",
    default_model="openrouter/google/gemini-flash-1.5",
    timeout=30,
    max_retries=5
)
```

## Backend Configuration

### Cloud Backend

Uses LiteLLM to provide unified access to multiple AI providers:

- **OpenRouter** (recommended): Access to 100+ models through single API key
- **OpenAI**: GPT-3.5, GPT-4, and newer models
- **Anthropic**: Claude models
- **Google**: Gemini models

### Local Backend

Uses Ollama for privacy-focused local inference:

```bash
# Configure Ollama URL (if not using default)
export OLLAMA_BASE_URL=http://localhost:11434

# Or via config
ttt config set ollama_base_url http://custom-server:11434
```

## Advanced Configuration

### Custom Backend Registration

```yaml
# In config file
backends:
  custom:
    class_path: mymodule.MyBackend
    config:
      api_key: xxx
      api_url: https://api.example.com
```

### Provider-Specific Settings

```yaml
backends:
  cloud:
    openai:
      organization: org-xxx
      api_base: https://custom-endpoint.com
    anthropic:
      api_version: 2023-06-01
```

### Rate Limiting Configuration

```yaml
rate_limits:
  openrouter: 60  # requests per minute
  openai: 120
  anthropic: 100
  
retry_config:
  max_attempts: 3
  backoff_factor: 2
  max_wait: 60
```

## Configuration Best Practices

1. **Use environment variables for API keys** - Keep sensitive data out of config files
2. **Create project-specific configs** - Use `./ttt.yaml` for project settings
3. **Set reasonable timeouts** - Balance between reliability and responsiveness
4. **Configure model aliases** - Create shortcuts for frequently used models
5. **Enable fallbacks** - Ensure reliability with automatic backend switching

## Troubleshooting

### Check Current Configuration
```bash
# View all settings
ttt config

# Check specific backend status
ttt status

# List available models
ttt models
```

### Common Issues

**API Key Not Found**
```bash
# Check if key is set
echo $OPENAI_API_KEY

# Set via config
ttt config set openai_key sk-...

# Or export directly
export OPENAI_API_KEY=sk-...
```

**Wrong Default Model**
```bash
# Check current default
ttt config get models.default

# Set new default
ttt config set models.default gpt-4
```

**Configuration Not Loading**
```bash
# Check config file locations
ls -la ~/.config/ttt/config.yaml
ls -la ./ttt.yaml

# Verify syntax
python -m yaml < ttt.yaml
```