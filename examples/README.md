# AI Library Examples

This directory contains comprehensive examples demonstrating how to use the AI library effectively. The examples are organized progressively, from basic usage to advanced features.

## 📚 Examples Overview

### 01_basic_usage.py
**Perfect starting point for new users**
- Basic `ask()` and `stream()` functions
- Simple chat sessions
- Model selection and backend routing
- Basic error handling

### 02_tools_and_workflows.py
**Comprehensive tools and workflows guide**
- Built-in tools discovery and usage
- File operations, web search, calculations
- Code execution and API requests
- Custom tools with `@tool` decorator
- Complex multi-tool workflows
- CLI usage examples

### 03_chat_and_persistence.py
**Advanced chat and session management**
- Basic and persistent chat sessions
- Saving and loading conversations
- Multi-session management
- Chat sessions with tools
- Incremental conversations
- Cost tracking and session analytics

### 04_advanced_features.py
**Production-ready patterns and advanced features**
- Multi-modal AI (vision capabilities)
- Comprehensive exception handling
- Production error handling patterns
- Robust retry logic
- Configuration management
- Best practices guide

## 🚀 Quick Start

### Prerequisites
You'll need either:
- **Local setup**: Ollama running locally
- **Cloud setup**: API keys configured (OpenAI, Anthropic, Google, etc.)

### Running Examples

1. **With real backends** (recommended for full experience):
   ```bash
   # Make sure you have API keys set up
   export OPENAI_API_KEY="your-key-here"
   export ANTHROPIC_API_KEY="your-key-here"
   
   # Run examples
   python3 01_basic_usage.py
   python3 02_tools_and_workflows.py
   python3 03_chat_and_persistence.py
   python3 04_advanced_features.py
   ```

2. **With mock backend** (for testing/development):
   ```bash
   # Use the provided helper script
   python3 run_example.py 01_basic_usage
   python3 run_example.py 02_tools_and_workflows
   python3 run_example.py 03_chat_and_persistence
   python3 run_example.py 04_advanced_features
   ```

3. **Validate syntax and imports**:
   ```bash
   python3 validate_examples.py
   ```

## 🛠️ Development Tools

### test_examples.py
Comprehensive test suite that validates:
- Core AI functions work correctly
- All examples can be imported
- Required dependencies are available
- Custom tools and advanced features work

### run_example.py
Helper script that:
- Sets up mock backend automatically
- Runs examples safely without requiring real API keys
- Handles import paths correctly

### validate_examples.py
Validation tool that checks:
- Python syntax is correct
- All imports are valid
- AI functions are used properly
- Examples follow best practices

## 🔧 Extensions

### plugins/ Directory
Contains example plugins for extending the library:
- **mock_llm_backend.py**: Mock backend for testing
- **echo_backend.py**: Simple echo backend example
- **README.md**: Plugin development guide

## 📖 Learning Path

**Recommended progression:**

1. **Start with 01_basic_usage.py**
   - Learn core functions: `ask()`, `stream()`, `chat()`
   - Understand model selection and routing
   - Get familiar with basic error handling

2. **Move to 02_tools_and_workflows.py**
   - Discover built-in tools
   - Learn to create custom tools
   - Build complex workflows
   - Understand CLI usage

3. **Progress to 03_chat_and_persistence.py**
   - Master chat sessions
   - Learn persistence patterns
   - Implement multi-session apps
   - Track usage and costs

4. **Finish with 04_advanced_features.py**
   - Add vision capabilities
   - Implement robust error handling
   - Apply production patterns
   - Follow best practices

## 🎯 Key Concepts

### Backend Selection
- **Local**: Uses Ollama for privacy and offline usage
- **Cloud**: Uses OpenAI, Anthropic, Google for best performance
- **Mock**: Uses fake responses for testing and development

### Model Routing
The library automatically selects the best model based on:
- Query type (code, math, analysis, etc.)
- Performance preferences (fast vs. quality)
- Backend availability

### Error Handling
Examples demonstrate:
- Specific exception handling
- Graceful fallbacks
- Retry logic for rate limits
- Production-ready patterns

### Tools System
- **Built-in tools**: Web search, file operations, calculations
- **Custom tools**: Create domain-specific functionality
- **Tool chaining**: Complex workflows with multiple tools

## 🔍 Troubleshooting

### Common Issues

1. **Import errors**:
   ```bash
   # Make sure you're in the right directory
   cd /path/to/ai-library
   python3 examples/01_basic_usage.py
   ```

2. **API key errors**:
   ```bash
   # Check your environment variables
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY
   
   # Or use mock backend for testing
   python3 examples/run_example.py 01_basic_usage
   ```

3. **Backend connection errors**:
   ```bash
   # For local backend, make sure Ollama is running
   ollama serve
   
   # For cloud backend, check your API keys
   python3 -c "import os; print('OPENAI_API_KEY' in os.environ)"
   ```

### Getting Help

- Check the main project README for setup instructions
- Look at the `docs/` directory for detailed documentation
- Run `python3 validate_examples.py` to check your setup
- Use the mock backend for testing without API costs

## 📝 Contributing

When adding new examples:

1. Follow the existing naming pattern: `NN_description.py`
2. Include comprehensive docstrings
3. Add error handling examples
4. Test with both real and mock backends
5. Update this README with new examples

## 🎉 What's New

This is the **consolidated version** of the examples, designed to provide a much better learning experience:

- **4 focused files** instead of 8 scattered ones
- **Progressive learning path** from basic to advanced
- **Comprehensive coverage** of each topic
- **Better organization** with related concepts grouped together
- **Cross-references** between examples
- **Production-ready patterns** throughout

The examples have been reorganized as follows:
- `basic_usage.py` → `01_basic_usage.py` (simplified)
- `builtin_tools_demo.py` + `chat_with_tools.py` → `02_tools_and_workflows.py`
- `persistent_chat.py` + chat components → `03_chat_and_persistence.py`
- `multi_modal.py` + `exception_handling.py` → `04_advanced_features.py`

Happy coding! 🚀