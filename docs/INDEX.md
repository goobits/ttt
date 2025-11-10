# Documentation Guide

Welcome to Goobits TTT documentation! This guide helps you find exactly what you need.

## Quick Start

**New to TTT?** Start here:
1. [Configuration Guide](./configuration.md) - Set up API keys and basic config
2. [API Reference](./api-reference.md) - Learn core functions: `ask()`, `stream()`, `chat()`

**Contributing or developing?** Start here:
1. [Development Guide](./development.md) - Setup, testing, and workflow
2. [Architecture Guide](./architecture.md) - Understand the system design

## By Role

### 👤 End Users
Start with these docs in order:
- **[Configuration Guide](./configuration.md)** (5 min) - Essential setup
- **[API Reference](./api-reference.md)** (15 min) - Core functionality
- **[Extensibility Guide](./extensibility.md)** (10 min) - Advanced customization

### 💻 Contributors & Developers
Recommended reading order:
- **[Development Guide](./development.md)** (10 min) - Dev setup and workflow
- **[Architecture Guide](./architecture.md)** (15 min) - System design patterns
- **[API Reference](./api-reference.md)** (10 min) - Implementation details
- **[Extensibility Guide](./extensibility.md)** (15 min) - Plugin system

### 🔧 Power Users
Jump to what you need:
- Custom backends → [Extensibility Guide](./extensibility.md#custom-backends)
- Custom tools → [Extensibility Guide](./extensibility.md#custom-tools)
- Advanced config → [Configuration Guide](./configuration.md#advanced-configuration)
- CLI development → [Development Guide](./development.md#adding-cli-commands)

## By Task

### Setting Up
- **Install and configure** → [Development Guide: Installation](./development.md#installation)
- **Set API keys** → [Configuration Guide: API Keys](./configuration.md#api-keys)
- **Run tests** → [Development Guide: Testing](./development.md#testing)

### Using TTT
- **Make AI requests** → [API Reference: Core Functions](./api-reference.md#core-functions)
- **Stream responses** → [API Reference: Streaming](./api-reference.md#streaming-api)
- **Manage conversations** → [API Reference: Chat Sessions](./api-reference.md#chat-sessions)
- **Use tools/function calling** → [API Reference: Tools](./api-reference.md#tools-and-function-calling)

### Extending TTT
- **Add custom backend** → [Extensibility Guide: Custom Backends](./extensibility.md#custom-backends)
- **Create custom tools** → [Extensibility Guide: Custom Tools](./extensibility.md#custom-tools)
- **Add custom models** → [Extensibility Guide: Model Registry](./extensibility.md#model-registry)
- **Plugin development** → [Extensibility Guide: Plugins](./extensibility.md#plugin-system)

### Development
- **Add CLI command** → [Development Guide: CLI Commands](./development.md#adding-cli-commands)
- **Write tests** → [Development Guide: Writing Tests](./development.md#writing-tests)
- **Debug issues** → [Development Guide: Debugging](./development.md#debugging)
- **Code style** → [Development Guide: Code Quality](./development.md#code-quality)

### Understanding Internals
- **System architecture** → [Architecture Guide](./architecture.md#architecture-overview)
- **Backend system** → [Architecture Guide: Backends](./architecture.md#backend-system)
- **Routing logic** → [Architecture Guide: Routing](./architecture.md#routing-system)
- **Configuration hierarchy** → [Architecture Guide: Config](./architecture.md#configuration-system)

## Complete Documentation List

| Document | Purpose | Audience | Est. Time |
|----------|---------|----------|-----------|
| **[api-reference.md](./api-reference.md)** | Complete Python API documentation | Users, Developers | 15-20 min |
| **[configuration.md](./configuration.md)** | Configuration system and options | All users | 10 min |
| **[development.md](./development.md)** | Development setup and workflow | Contributors | 15 min |
| **[architecture.md](./architecture.md)** | System design and patterns | Developers, Contributors | 20 min |
| **[extensibility.md](./extensibility.md)** | Custom backends, tools, plugins | Power users, Developers | 20 min |
| **[GLOSSARY.md](./GLOSSARY.md)** | Key terms and concepts | All users | 5 min |

## Key Concepts

Not sure what a term means? See the **[Glossary](./GLOSSARY.md)** for definitions of:
- Backend, Provider, Router
- Response, Session, Tool
- Model, Plugin, Hook

## Getting Help

- **Issues**: Report bugs at [github.com/goobits/ttt/issues](https://github.com/goobits/ttt/issues)
- **Discussions**: Ask questions in GitHub Discussions
- **Contributing**: See [Development Guide](./development.md)

---

**Tip**: Use your browser's search (Ctrl/Cmd+F) to find specific topics within documents.
