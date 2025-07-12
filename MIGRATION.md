# Migration Plan: Deprecating `/llm` in Favor of Enhanced `/agents`

## Overview

This document outlines the plan to enhance the `/agents` AI library to absorb all functionality from the separate `/llm` CLI tool, providing a unified AI interface that serves both simple and advanced use cases.

## Current State

### `/llm` Tool Strengths
- ✅ Zero-config setup for local usage
- ✅ Simple CLI interface: `llm "question"`
- ✅ Excellent Unix pipe integration
- ✅ Privacy-first (offline-only) workflow
- ✅ Optimized for latest local models (Qwen 2.5)

### `/agents` Library Strengths  
- ✅ Comprehensive AI provider support (OpenAI, Anthropic, Google, etc.)
- ✅ Advanced tool/function calling system
- ✅ Persistent chat sessions
- ✅ Rich Python API (sync + async)
- ✅ Extensive error handling and recovery
- ✅ Plugin system and extensibility

### The Gap
The `/llm` tool serves users who want simple, privacy-first AI queries without complex setup, while `/agents` serves users building AI applications. There's currently no unified solution.

## Migration Goals

1. **Absorb `/llm` functionality** into `/agents` without breaking existing APIs
2. **Provide simple CLI mode** that matches `/llm`'s ease of use
3. **Maintain user choice** between offline and online backends
4. **No forced installations** - respect user storage and privacy preferences
5. **Enable smooth migration path** from `/llm` to enhanced `/agents`

## Proposed Enhancements

### 1. Enhanced CLI Interface

#### New Simple Mode
```bash
# Basic usage (auto-detects best available backend)
ai "What is quantum computing?"
ai --code "Write a Python function to sort a list"

# Backend shortcuts
ai "question" --offline          # Force offline/local models
ai "question" --online           # Force online/cloud models

# Specific model selection (precise control)
ai "question" --model gpt-4o-mini                    # Specific cloud model
ai "question" --model llama3:8b-instruct-q5_K_M     # Exact local model with quantization
ai "question" --model claude-3-5-sonnet-20241022    # Specific model version

# Interactive chat mode (NEW)
ai --chat                        # Start persistent conversation
ai --chat --model gpt-4          # Chat with specific model
ai --chat --offline              # Private offline chat session
ai --chat --code                 # Coding-focused chat session

# Enhanced pipe support
cat script.py | ai --code "review this code for bugs"
docker logs myapp | ai "analyze these error patterns"
```

#### Flexible Flag Positioning
```bash
# All equivalent (matches llm behavior)
ai "write a function" --code
ai --code "write a function"  
ai "write" --code "a function"

# Chat mode combinations
ai --chat --code --offline      # Start offline coding chat
ai --offline --chat --model llama3:8b-instruct-q5_K_M  # Specific model chat
```

### 2. Smart Backend Detection

#### Auto-Configuration Logic
1. **Explicit choice** (`--offline`, `--online`, `--model`, `--chat`) → Use specified
2. **Simple mode** → Auto-detect best available (API keys OR Ollama)
3. **Chat mode** → Start persistent session with chosen backend/model
4. **Nothing available** → Show helpful setup guidance

#### No Forced Installations
- Detect existing Ollama installations and models
- Detect configured API keys
- Provide clear setup guidance without auto-installing
- Respect user storage and privacy preferences

### 3. Enhanced User Experience

#### First-Run Experience
```bash
$ ai "hello"
❌ No AI backends configured.

Setup options:
1. Online AI (requires API key): See README.md for API key setup
2. Offline AI (requires Ollama): curl -fsSL https://ollama.com/install.sh | sh
3. Both: Configure API keys AND install Ollama for maximum flexibility

Choose your preferred setup and try again.
```

#### Coding Detection
- Smart detection of coding-related queries
- Automatic selection of coding-optimized models when available
- File extension detection from piped input

#### Error Handling
- Clear, actionable error messages
- Suggestions for missing dependencies
- No technical jargon in simple mode

### 4. API Implementation

#### New CLI Functions
```python
# ai/cli.py enhancements
def detect_simple_usage(args) -> bool
def handle_simple_mode(args) -> str
def handle_chat_mode(args) -> None  # NEW: Interactive chat sessions
def detect_available_backends() -> List[str]
def suggest_setup_options() -> None
def smart_model_selection(prompt: str, backend: str) -> str
def parse_precise_model_name(model: str) -> Tuple[str, Dict[str, Any]]  # NEW: Handle exact model specs
```

#### Enhanced Backend Detection
```python
# ai/backends/local.py enhancements  
async def detect_ollama() -> bool
async def list_available_models() -> List[str]
async def suggest_best_model(prompt: str) -> str
async def validate_precise_model(model: str) -> bool  # NEW: Validate exact model names

# ai/backends/cloud.py enhancements
def detect_configured_providers() -> List[str]
def suggest_best_cloud_model(prompt: str) -> str
def resolve_model_alias(model: str) -> str  # NEW: Handle provider-specific model names
```

#### Smart Routing
```python
# ai/routing.py new module
def auto_select_backend(available_backends: List[str]) -> str
def is_coding_request(prompt: str, context: dict) -> bool
def select_optimal_model(prompt: str, backend: str) -> str

# NEW: Chat session management
# ai/chat.py enhancements
def create_cli_chat_session(model: str = None, backend: str = None) -> PersistentChatSession
def handle_interactive_chat(session: PersistentChatSession) -> None
```

## Implementation Plan

### Phase 1: Core CLI Enhancements (Week 1-2)
- [ ] Implement simple CLI mode detection
- [ ] Add `--offline` and `--online` flags
- [ ] Add `--chat` flag for interactive sessions
- [ ] Implement precise `--model` flag with exact model name support
- [ ] Enhance pipe support and flexible flag positioning
- [ ] Implement smart backend detection without auto-installation
- [ ] Add friendly error messages and setup guidance

### Phase 2: Smart Features (Week 3)
- [ ] Implement coding request detection
- [ ] Add smart model selection for available backends
- [ ] Build interactive chat mode with session persistence
- [ ] Add model validation for precise model names (quantization, versions)
- [ ] Enhance stdin handling and file type detection
- [ ] Add performance optimizations for simple mode

### Phase 3: Documentation & Migration (Week 4)
- [ ] Update `/agents` README with simple usage examples
- [ ] Create migration guide from `/llm` to `/agents`
- [ ] Add deprecation notice to `/llm` README
- [ ] Create troubleshooting guide for common issues

### Phase 4: Deprecation Timeline
- **Month 1**: Soft deprecation - add notice to `/llm` about migration path
- **Month 2**: Hard deprecation - replace `/llm` README with migration guide
- **Month 3**: Remove `/llm` directory after confirming no usage

## API Changes

### No Breaking Changes
- All existing `/agents` APIs remain unchanged
- Current configuration and usage patterns preserved
- Existing integrations continue to work

### New APIs Added
```python
# Enhanced configuration
def detect_available_backends() -> List[str]
def auto_configure_simple_mode() -> bool

# Smart routing  
def smart_route(prompt: str, prefer_offline: bool = False) -> Tuple[str, str]
def suggest_optimal_model(prompt: str, available_models: List[str]) -> str

# CLI enhancements
def parse_flexible_args(args: List[str]) -> Dict[str, Any]
def handle_simple_interface(args: Dict[str, Any]) -> str
def handle_chat_interface(args: Dict[str, Any]) -> None  # NEW: Interactive chat

# Model precision support
def parse_precise_model_spec(model: str) -> ModelSpec  # NEW: Handle exact model formats
def validate_model_availability(model: str, backend: str) -> bool  # NEW: Model validation
```

### Enhanced Existing APIs
- `ai/cli.py`: Better argument parsing, chat mode, and user experience
- `ai/backends/local.py`: Enhanced Ollama detection, precise model validation
- `ai/backends/cloud.py`: Better model name resolution and provider-specific handling
- `ai/chat.py`: CLI integration for interactive sessions
- `ai/config.py`: Auto-configuration for simple usage scenarios

## Success Metrics

### Technical Success
- [ ] 100% feature parity with current `/llm` tool
- [ ] Zero breaking changes to existing `/agents` APIs
- [ ] Simple mode works without configuration when backends available
- [ ] Interactive chat mode provides persistent conversations
- [ ] Precise model specification works with exact Ollama model names
- [ ] Enhanced pipe support matches or exceeds `/llm` functionality

### User Experience Success
- [ ] New users can start with `ai "question"` immediately if backends available
- [ ] Chat mode provides intuitive interactive experience (`ai --chat`)
- [ ] Power users can specify exact models with full precision
- [ ] Clear setup guidance when no backends configured
- [ ] Smooth migration path from `/llm` with no functionality loss
- [ ] Advanced features discoverable but not overwhelming

### Migration Success
- [ ] `/llm` users successfully migrate to enhanced `/agents`
- [ ] No user complaints about loss of functionality
- [ ] Positive feedback on enhanced features and UX
- [ ] Clean deprecation with clear communication

## Risks and Mitigation

### Risk: Complexity Creep
**Mitigation**: Maintain clear separation between simple and advanced modes. Simple mode hides complexity by default.

### Risk: Breaking Existing Users
**Mitigation**: Zero breaking changes policy. All enhancements are additive.

### Risk: Poor Migration Experience  
**Mitigation**: Comprehensive testing with actual `/llm` users. Clear documentation and migration guides.

### Risk: Backend Detection Issues
**Mitigation**: Robust detection logic with fallbacks. Clear error messages when detection fails.

## Post-Migration Benefits

### For `/llm` Users
- Same simple interface they know and love
- NEW: Interactive chat mode for persistent conversations
- NEW: Precise model control (e.g., `llama3:8b-instruct-q5_K_M`)
- Enhanced pipe support and flexible flag positioning
- Better error handling and setup guidance
- Optional access to advanced features when needed
- Continued maintenance and feature updates

### For `/agents` Users
- Simplified entry point for new users
- Better local/offline model integration with precise control
- Enhanced CLI experience with chat mode
- Unified tool for all AI workflows (one-shot + interactive)
- Reduced maintenance burden (one tool instead of two)

### For Project Maintenance
- Single codebase to maintain and update
- Unified documentation and support
- Clearer project identity and messaging
- Better resource allocation and development focus

## Quick Migration Guide for `/llm` Users

### What Changes
```bash
# OLD llm usage
llm "question"
llm --code "coding question"
cat file.py | llm --code "review this"

# NEW ai usage (drop-in replacement)
ai "question" 
ai --code "coding question"
cat file.py | ai --code "review this"
```

### What's New
```bash
# Interactive chat (NEW)
ai --chat                        # Start conversation
ai --chat --offline              # Private chat

# Precise model control (NEW)  
ai "question" --model llama3:8b-instruct-q5_K_M
ai --chat --model gpt-4o-mini

# Backend choice (NEW)
ai "question" --offline          # Force local models
ai "question" --online           # Force cloud models
```

### Migration Steps
1. **Install enhanced agents**: `cd /agents && pip install -e .`
2. **Test compatibility**: `ai "hello world"` (should work like `llm`)
3. **Try new features**: `ai --chat` for interactive mode
4. **Uninstall old tool**: Remove `/llm` when ready

## Conclusion

This migration plan enhances the `/agents` library to serve both simple and advanced AI use cases, providing a smooth migration path for `/llm` users while maintaining all existing functionality. The result is a more cohesive, user-friendly AI toolkit that respects user choice and privacy preferences.

The implementation prioritizes user experience and backward compatibility, ensuring that both existing `/agents` users and `/llm` users benefit from the enhanced unified interface.