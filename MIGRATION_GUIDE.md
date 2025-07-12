# Migration Guide: From `llm` to Enhanced `ai`

## Quick Migration

**TL;DR**: Replace `llm` with `ai` and get enhanced features for free!

```bash
# Before (llm)
llm "What is Python?"

# After (ai) - same simplicity, more power
ai "What is Python?"
```

## Feature Comparison

| Feature | `llm` | Enhanced `ai` | Notes |
|---------|--------|---------------|-------|
| Basic queries | `llm "question"` | `ai "question"` | ✅ Drop-in compatible |
| Pipe support | `cat file \| llm "review"` | `cat file \| ai "review"` | ✅ Same functionality |
| Model selection | `llm -m model "question"` | `ai --model model "question"` | ✅ Compatible |
| **Backend control** | ❌ Not available | `ai "question" --offline` | 🆕 Force local/cloud |
| **Coding mode** | ❌ Not available | `ai "code question" --code` | 🆕 Auto-optimization |
| **Interactive chat** | ❌ Not available | `ai --chat` | 🆕 Coming soon |
| **Smart detection** | ❌ Not available | Auto-detects coding requests | 🆕 Automatic |
| **Rich output** | Basic text | Rich formatting + metadata | 🆕 Enhanced UX |
| **Setup guidance** | ❌ Not available | Helpful error messages | 🆕 Better DX |

## Migration Steps

### 1. Install Enhanced AI

```bash
cd /path/to/agents
./setup.sh install
```

### 2. Configure API Keys

Same as before - edit `.env` file:

```bash
# OpenRouter (recommended)
OPENROUTER_API_KEY=your-key-here

# Or direct provider keys
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
```

### 3. Test Basic Functionality

```bash
# Test your existing workflow
ai "What is 2+2?"                # Should work like llm

# Check what's available
ai backend-status                # See configured backends
ai models-list                   # See available models
```

### 4. Try Enhanced Features

```bash
# Force backend selection
ai "private question" --offline   # Use local Ollama models
ai "complex analysis" --online    # Use cloud models

# Coding assistance
ai "write a hello world function" --code

# Verbose mode for debugging
ai "test question" --verbose

# Flexible flag positioning
ai --code "write a function" --verbose
```

## Command Mapping

### Basic Usage
```bash
# llm → ai (direct replacement)
llm "question"              →  ai "question"
llm "question" -v           →  ai "question" --verbose
llm -m gpt-4 "question"     →  ai --model gpt-4 "question"
```

### Enhanced Usage
```bash
# New features not available in llm
ai "question" --offline                    # Force local backend
ai "question" --online                     # Force cloud backend  
ai "write code" --code                     # Coding optimization
ai --code "write" --verbose "a function"  # Flexible positioning
```

### Pipe Support
```bash
# Same functionality
cat file.py | llm "review this"     →  cat file.py | ai "review this"
echo "code" | llm -                 →  echo "code" | ai -

# Enhanced with coding detection
cat script.py | ai "review this code" --code
```

## New Features to Explore

### 1. Smart Backend Selection
```bash
# Automatically chooses best available backend
ai "question"                    # Auto-detects cloud/local

# Manual control
ai "sensitive data" --offline    # Keep private with local models
ai "complex task" --online       # Use powerful cloud models
```

### 2. Coding Optimization
```bash
# Automatic detection
ai "debug this function"         # Auto-detects coding context

# Manual optimization
ai "help with Python" --code     # Force coding mode
ai --code "write a sort function" --verbose
```

### 3. Enhanced Error Handling
```bash
# If no backends configured:
ai "test"
# ❌ No AI backends configured.
# 
# Setup Options:
# 1. Online AI (requires API key): ...
# 2. Offline AI (requires Ollama): ...
```

### 4. Rich Output
```bash
ai "What is 2+2?" --verbose
# ╭─────────────── AI Request ───────────────╮
# │ Prompt: What is 2+2?                     │
# │ Backend: cloud                            │
# ╰───────────────────────────────────────────╯
# 
# 2 + 2 = 4
# 
# ╭────────── Response Metadata ─────────────╮
# │ Model: openrouter/google/gemini-flash-1.5│
# │ Backend: cloud                            │
# │ Time: 0.74s                              │
# │ Tokens In: 7                             │
# │ Tokens Out: 8                            │
# ╰───────────────────────────────────────────╯
```

## Troubleshooting

### Common Issues

**"Command not found: ai"**
```bash
# Restart terminal or source bashrc
source ~/.bashrc

# Check installation
which ai
```

**"No AI backends configured"**
```bash
# Check status
ai backend-status

# Verify .env file
cat .env

# Add missing API keys
echo "OPENROUTER_API_KEY=your-key" >> .env
```

**"Model not found"**
```bash
# List available models
ai models-list

# Use a known working model
ai "test" --model openrouter/google/gemini-flash-1.5
```

### Performance

The enhanced `ai` tool should match or exceed `llm` performance:
- Same response times for basic queries
- Enhanced features (auto-detection, rich output) add minimal overhead
- Smart caching and connection pooling for better performance

## What's Coming

Features in development:
- **Interactive chat mode**: `ai --chat` for persistent conversations
- **Precise model validation**: Support exact Ollama model names
- **Advanced routing**: Automatic fallback when backends fail
- **Extended tool integration**: More built-in tools and better tool chaining

## Need Help?

- **Check status**: `ai backend-status`
- **List models**: `ai models-list`  
- **Show help**: `ai --help`
- **Verbose mode**: Add `--verbose` to any command for detailed info

---

**Migration complete!** You now have a more powerful AI CLI with the same simplicity you're used to.