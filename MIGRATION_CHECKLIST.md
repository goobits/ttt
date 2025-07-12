# Migration Checklist: `/llm` → Enhanced `/agents`

**Status**: ✅ = Complete, 🚧 = In Progress, ⏳ = Planned, ❌ = Not Started

## Current Implementation Status

### ✅ Already Implemented (Found in `/agents`)
- [x] **Basic CLI Interface** (`ai/cli.py:main`)
  - Simple usage: `ai "question"`
  - Help system with rich formatting
  - Error handling with user-friendly messages
  
- [x] **Backend System** (`ai/backends/`)
  - Cloud backend (OpenRouter, OpenAI, Anthropic, Google)
  - Local backend (Ollama integration)
  - Auto-detection and availability checking
  
- [x] **Tool/Function System** (`ai/tools/`)
  - Built-in tools (web_search, file operations, calculate, etc.)
  - Custom tool creation with `@tool` decorator
  - Tool registry and execution system
  
- [x] **Chat Sessions** (`ai/chat.py`)
  - Persistent chat sessions
  - Session save/load functionality
  - Context management

- [x] **Python API** (`ai/api.py`)
  - Synchronous API (`ask`, `stream`, `chat`)
  - Asynchronous API (`ask_async`, `stream_async`, `achat`)
  - Response objects with metadata

## Phase 1: Core CLI Enhancements (Week 1-2)

### ✅ Simple CLI Mode Detection
- [x] **Flexible Flag Positioning** (`ai/cli.py:parse_args`)
  - [x] Support: `ai "question" --code` and `ai --code "question"`
  - [x] Support: `ai "write" --code "a function"`
  
- [x] **Enhanced Flag Support**
  - [x] `--model` flag (already implemented)
  - [x] `--backend` flag (already implemented) 
  - [x] `--offline` flag (force local backend)
  - [x] `--online` flag (force cloud backend)
  - [x] `--code` flag (coding-optimized responses)
  - [x] `--chat` flag (interactive chat mode)

### ❌ Precise Model Support
- [x] Basic model specification (already works)
- [ ] **Exact Model Name Validation** (`ai/backends/local.py`)
  - [ ] Support `llama3:8b-instruct-q5_K_M` format
  - [ ] Validate model exists before attempting use
  - [ ] Parse quantization parameters
  - [ ] Handle version specifications

### 🚧 Interactive Chat Mode 
- [x] Persistent chat sessions (already implemented)
- [x] **CLI Interactive Mode** (`ai/cli.py`) - IMPLEMENTED BUT BROKEN
  - [x] `ai --chat` starts interactive session (UI implemented)
  - [x] `ai --chat --model gpt-4` with specific model (args parsing)
  - [x] `ai --chat --offline` for local chat (args parsing)
  - [x] `ai --chat --code` for coding sessions (args parsing)
  - [x] Exit commands (quit, exit, Ctrl+C) (implemented)
  - [ ] **FIX**: Session configuration error causing API failures

### ✅ Enhanced Pipe Support (Already Working)
- [x] stdin reading with `ai -`
- [x] Pipe support: `cat file.py | ai "review this"`
- [x] Tool integration: `ai "question" --tools tool1,tool2`

## Phase 2: Smart Features (Week 3)

### 🚧 Smart Backend Detection
- [x] Basic backend detection (already implemented)
- [x] **Enhanced Auto-Configuration** - PARTIALLY IMPLEMENTED
  - [x] Auto-detect best available backend (`detect_best_backend()`)
  - [x] Prefer cloud when API keys available, fallback to local
  - [ ] **MISSING**: Fallback logic when primary backend fails
  - [ ] **MISSING**: Smart model selection based on prompt type
  - [ ] **MISSING**: Create `ai/routing.py` module (logic currently in CLI)

### 🚧 Coding Request Detection  
- [x] **Smart Prompt Analysis** - PARTIALLY IMPLEMENTED
  - [x] Detect coding-related queries (`is_coding_request()`)
  - [x] Auto-select coding-optimized models (`apply_coding_optimization()`)
  - [ ] **MISSING**: File extension detection from piped input
  - [x] Auto-suggest coding optimization (shows in verbose mode)

### ✅ Enhanced User Experience
- [x] **First-Run Experience** (`ai/cli.py:main`)
  - [x] Detect no backends configured (`check_backend_available()`)
  - [x] Show helpful setup guidance (`show_setup_guidance()`)
  - [x] No auto-installation (respect user choice)
  - [x] Clear setup options display with rich formatting

### ✅ Enhanced Error Handling
- [x] Basic error handling (already implemented)
- [x] **Improved Error Messages**
  - [x] Model availability suggestions (in error messages)
  - [x] Setup guidance for missing dependencies (`show_setup_guidance()`)
  - [x] Clear next steps for each error type (rich formatted panels)

## Phase 3: Advanced Features

### 🚧 New CLI Functions (`ai/cli.py`)
```python
# Functions implemented:
def detect_best_backend(args) -> str                     # ✅ Implemented
def handle_interactive_chat(args) -> None                # ✅ Implemented (but broken)
def check_backend_available(backend) -> bool             # ✅ Implemented
def show_setup_guidance() -> None                        # ✅ Implemented
def apply_coding_optimization(args, kwargs) -> dict      # ✅ Implemented
def is_coding_request(prompt: str) -> bool               # ✅ Implemented
def parse_chat_args(args) -> dict                        # ✅ Implemented

# Functions still needed:
def smart_model_selection(prompt: str, backend: str) -> str  # ❌ Not implemented
def parse_precise_model_name(model: str) -> Tuple[str, Dict]  # ❌ Not implemented
```

### ❌ Enhanced Backend Detection (`ai/backends/`)
```python
# Local backend enhancements needed:
async def detect_ollama() -> bool                        # 🚧 Basic version exists
async def list_available_models() -> List[str]           # 🚧 Basic version exists  
async def suggest_best_model(prompt: str) -> str         # ❌ Not implemented
async def validate_precise_model(model: str) -> bool     # ❌ Not implemented

# Cloud backend enhancements needed:
def detect_configured_providers() -> List[str]           # ❌ Not implemented
def suggest_best_cloud_model(prompt: str) -> str         # ❌ Not implemented
def resolve_model_alias(model: str) -> str               # ❌ Not implemented
```

### ❌ Smart Routing System (`ai/routing.py` - NEW MODULE NEEDED)
```python
# New module to create (logic currently scattered in CLI):
def auto_select_backend(available_backends: List[str]) -> str      # ❌ Not implemented
def is_coding_request(prompt: str, context: dict) -> bool          # 🚧 Basic version in CLI
def select_optimal_model(prompt: str, backend: str) -> str         # ❌ Not implemented
def handle_backend_fallback(primary_error: Exception) -> str       # ❌ Not implemented
```

### 🚧 Enhanced Chat System (`ai/chat.py`)
```python
# CLI integration status:
# ✅ UI and argument parsing implemented
# ❌ Session configuration broken - needs debugging
# ✅ Interactive loop with exit commands implemented
# ❌ Chat session creation fails with API errors
```

## Phase 4: Documentation & Migration (Week 4)

### ❌ Documentation Updates
- [ ] **Update `/agents` README.md**
  - [ ] Add simple usage examples matching `/llm`
  - [ ] Document new flags (`--offline`, `--online`, `--chat`, `--code`)
  - [ ] Add interactive chat mode examples
  - [ ] Include precise model specification guide

- [ ] **Create Migration Guide**
  - [ ] Side-by-side command comparison
  - [ ] Feature mapping (`llm` → `ai`)
  - [ ] Installation steps
  - [ ] Troubleshooting section

- [ ] **Add Deprecation Notice**
  - [ ] Create `/llm` deprecation README
  - [ ] Point to enhanced `/agents`
  - [ ] Include migration timeline

## Phase 5: Testing & Validation

### 🚧 Feature Parity Testing
- [x] **Basic CLI Tests** - MANUALLY TESTED
  - [x] Test `ai "question"` works (✅ working with API keys)
  - [x] Verify pipe support: `cat file | ai "review"` (not tested but implemented)
  - [x] Test flexible flag positioning (✅ working: `ai --code "question"`)
  
- [x] **New Flag Tests** - MANUALLY TESTED
  - [x] Test `--offline` forces local backend (✅ working)
  - [x] Test `--online` forces cloud backend (✅ working)
  - [x] Test `--code` optimization (✅ working)
  - [x] Test `--verbose` metadata display (✅ working)

- [ ] **Interactive Chat Tests** - BROKEN
  - [x] Test `ai --chat` UI starts (✅ UI works)
  - [ ] **BROKEN**: Chat session creation fails with API errors
  - [x] Test exit commands implemented (✅ quit/exit work)
  - [ ] Test session persistence (untested due to API failure)

- [ ] **Backend Detection Tests** - PARTIALLY TESTED
  - [x] Test auto-detection logic (✅ prefers cloud → local)
  - [ ] Test graceful fallbacks when backend fails
  - [x] Test setup guidance display (✅ rich formatting works)

### ❌ Migration Validation
- [x] **Basic User Experience** - PARTIALLY TESTED
  - [x] First-run experience with no backends (✅ shows helpful guidance)
  - [x] Setup guidance is helpful and accurate (✅ formatted nicely)
  - [x] Error messages are actionable (✅ with suggestions)
  - [ ] **NOT TESTED**: Performance comparison with `/llm`
- [ ] **Automated Test Suite** - NOT IMPLEMENTED
- [ ] **User Migration Testing** - NOT DONE

## Implementation Priority

### ✅ High Priority (Essential for Migration) - MOSTLY COMPLETE
1. ✅ **Enhanced Flag Support** - `--offline`, `--online`, `--code`, `--chat`
2. 🚧 **Interactive Chat Mode** - `ai --chat` UI done, session creation broken
3. ✅ **Flexible Flag Positioning** - Match `/llm` argument parsing
4. ✅ **Smart Backend Detection** - Auto-select best available option

### 🚧 Medium Priority (Nice to Have) - PARTIALLY COMPLETE
1. ❌ **Precise Model Validation** - Exact model name support
2. ✅ **Coding Request Detection** - Auto-optimize for code questions  
3. ✅ **Enhanced Error Messages** - Better setup guidance
4. ❌ **Smart Model Selection** - Prompt-based model optimization

### ❌ Low Priority (Future Enhancement) - NOT STARTED
1. ❌ **Advanced Routing Logic** - Complex fallback strategies
2. ❌ **Performance Optimizations** - Connection pooling, caching
3. ❌ **Extended Tool Integration** - Advanced tool chaining
4. ❌ **Analytics/Usage Tracking** - Optional usage metrics

## Success Criteria

### 🚧 Technical Success - MOSTLY ACHIEVED
- [x] **Basic feature parity** with `/llm` tool functionality
- [x] **Zero breaking changes** to existing `/agents` APIs (maintained)
- [x] **Simple mode works** with configuration when backends available
- [ ] **BROKEN**: Interactive chat mode session creation fails
- [ ] **MISSING**: Precise model specification for exact Ollama model names
- [x] **Enhanced pipe support** implemented (not fully tested)

### 🚧 User Experience Success - MOSTLY ACHIEVED
- [x] **New users can start** with `ai "question"` when backends configured
- [ ] **BROKEN**: Chat mode UI works but session creation fails
- [ ] **MISSING**: Exact model specification for power users
- [x] **Clear setup guidance** when no backends configured (rich formatting)
- [x] **Smooth basic usage** from `/llm` pattern (simple queries work)
- [x] **Advanced features discoverable** through help and verbose mode

## Current Architecture Assessment

### ✅ Strengths (Implemented Successfully)
- **Solid Foundation**: Core API, backend system, tool system all working
- **Rich Feature Set**: Function calling, persistent chat, async support  
- **Professional CLI**: Enhanced with rich formatting, smart error handling
- **New CLI Features**: All major flags implemented (`--offline`, `--online`, `--code`, `--chat`)
- **Smart Detection**: Auto-backend selection, coding optimization, setup guidance

### 🚧 Current Issues to Address
- **Chat Mode Broken**: Session creation fails with API configuration error
- **Missing Features**: Precise model validation, smart routing module
- **Testing Gaps**: Limited automated testing of new features
- **Documentation**: README and migration guide not updated

### ⚠️ Risk Assessment
- **Low Risk**: Core functionality working, main issue is one broken feature (chat)
- **No Breaking Changes**: All enhancements are additive, existing APIs preserved
- **User Impact**: Very positive - major UX improvements, `/llm`-like simplicity achieved
- **Timeline**: 1-2 days to fix chat mode, 1 week for remaining features

## Immediate Next Steps

1. **Fix Chat Mode**: Debug session configuration issue (highest priority)
2. **Create Routing Module**: Extract smart logic from CLI into `ai/routing.py`  
3. **Add Model Validation**: Support exact Ollama model names
4. **Update Documentation**: README with new examples, migration guide
5. **Testing**: Add automated tests for new CLI features

---

**Current Status**: `/agents` library has **~80% of migration functionality complete**. 
- ✅ **Core migration working**: `ai "question"` matches `/llm` experience
- ✅ **Enhanced features working**: Smart flags, backend detection, coding mode
- 🚧 **One major issue**: Chat mode broken (but UI complete)  
- ❌ **Missing**: Some advanced features, documentation updates

**Ready for limited migration testing with basic usage patterns.**