# Proposal: Migrate CLI from Click to Google Fire

## Problem Statement

Our current Click-based CLI has become overly complex due to fighting against Click's POSIX-strict design. We have 50+ lines of fragile `sys.argv` manipulation just to support intuitive flag placement like `ttt "hello" --json`.

## Current Complexity Issues

1. **Complex argument parsing** - Manual `sys.argv` reordering in `cli_entry()`
2. **Fragile edge cases** - Model aliases + flags + different orderings
3. **Fighting the framework** - Click enforces options-before-args, but users expect flexibility
4. **Hard to maintain** - Adding new flag combinations requires updating multiple parsing paths

## Proposed Solution: Google Fire

### Why Fire is Perfect for TTT

1. **Zero position restrictions** - Flags can go anywhere naturally
2. **Maintains all current syntax** - Everything that works now will still work
3. **Dramatically simpler code** - Eliminates most parsing complexity
4. **Better UX** - Users can put flags wherever feels natural

### Current Syntax Preservation

All existing syntax would work identically:

```bash
# Direct prompts (all current variations work)
ttt "hello world"
ttt --json "hello world" 
ttt "hello world" --json
ttt "hello world" --json --verbose

# Model aliases (all current variations work)
ttt @flash "hello"
ttt @flash "hello" --json
ttt --json @flash "hello"
ttt @claude "explain AI" --temperature=0.5 --json

# Subcommands
ttt status --json
ttt models --json
ttt config get models.default --json
```

### Fire Implementation Overview

```python
import fire

class TTT:
    def __init__(self):
        # Initialize once
        pass
    
    def __call__(self, *args, model=None, system=None, temperature=None, 
                 max_tokens=None, tools=None, stream=False, verbose=False, 
                 debug=False, code=False, json=False):
        """Main prompt handler - supports @model syntax and flexible flags"""
        
        # Handle @model syntax (simple 3-line conversion)
        if args and args[0].startswith('@'):
            model = args[0][1:]  # Extract model name
            prompt = ' '.join(args[1:])
        else:
            prompt = ' '.join(args)
        
        # Call existing ask_command logic
        return ask_command(prompt, model, system, temperature, max_tokens, 
                          tools, stream, verbose, code, json)
    
    def status(self, json=False):
        """Backend status"""
        return show_backend_status(json)
    
    def models(self, json=False):
        """List available models"""
        return show_models_list(json)
    
    def config(self, action=None, key=None, value=None, reset=False, json=False):
        """Configuration management"""
        # Existing config logic with JSON support
        
    def chat(self, resume=False, session_id=None, list_sessions=False, 
             model=None, system=None, tools=None):
        """Interactive chat mode"""
        # Existing chat logic

def main():
    fire.Fire(TTT)
```

## Benefits

### 1. Massive Code Simplification
- **Remove** entire `cli_entry()` function (50+ lines)
- **Remove** complex `sys.argv` manipulation
- **Remove** argument reordering logic
- **Simpler** subcommand handling

### 2. Better User Experience
```bash
# All of these work naturally (no special parsing needed):
ttt "hello" --json --model=flash --temperature=0.1 --verbose
ttt --json --verbose "hello" --model flash --temperature 0.1
ttt --temperature=0.1 "hello" --json --model=flash --verbose
```

### 3. Maintained Compatibility
- **100% backward compatible** - all existing syntax preserved
- **@model syntax** - simple 3-line conversion (vs current 30+ lines)
- **All flags work anywhere** - no position restrictions

### 4. Easier Testing
- Fire handles argument parsing edge cases
- Focus testing on business logic, not CLI parsing
- Fewer brittle tests for argument combinations

## Implementation Plan

### Phase 1: Core Migration
1. Replace Click decorators with Fire class
2. Move existing command logic into Fire methods
3. Add simple @model handling (3 lines vs current 30+)
4. Comprehensive testing of all current syntax

### Phase 2: Cleanup
1. Remove `cli_entry()` function
2. Remove `sys.argv` manipulation code
3. Simplify argument handling throughout
4. Update tests to be less brittle

### Phase 3: Enhancement
1. Add any new flag combinations easily
2. Improve help generation
3. Better error messages

## Risk Assessment

### Low Risk
- Fire is mature, stable, and widely used (Google's official library)
- Maintains 100% syntax compatibility
- Can be implemented incrementally
- Easy rollback if needed

### Migration Effort
- **Estimated**: 2-3 hours of focused work
- **Complexity**: Low (mostly moving existing logic into Fire methods)
- **Testing**: Comprehensive (ensure all syntax variations work)

## Recommendation

**Strongly recommend migration to Fire** because:

1. **Eliminates current complexity** without losing any functionality
2. **Improves user experience** significantly
3. **Makes future CLI enhancements** much easier
4. **Reduces maintenance burden** dramatically

The current Click implementation is fighting against the framework's design. Fire aligns perfectly with TTT's goal of intuitive, flexible CLI interaction.

## Next Steps

1. **Approve proposal** and migration plan
2. **Create Fire branch** for implementation
3. **Comprehensive testing** of all syntax variations
4. **Deploy and monitor** for any edge cases

---

*This migration would solve the CLI complexity issues while maintaining all current functionality and improving the user experience.*