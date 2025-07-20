# PROPOSAL_CLI.md - TTT CLI Redesign

## Executive Summary

This proposal outlines a redesign of the TTT CLI to improve usability while maintaining power. The goal is to create a more intuitive, discoverable API that scales from simple use cases to advanced workflows.

## Current State

### Strengths
- Simple default: `ttt "prompt"`
- Comprehensive feature set (17+ options)
- Pipeline compatible
- JSON output for automation

### Pain Points
- Flag overload: 17+ options can overwhelm users
- Model selection requires memorizing long strings: `openrouter/google/gemini-flash-1.5`
- No session management for chat mode
- Mix of flags that don't compose well (`--chat` with `--json`)
- No configuration management beyond environment variables
- Duplicate flags (`-m/--model`, `-s/--system`, `-t/--temperature`)

## Proposed Changes

### 1. Model Selection Shortcuts

**Current:**
```bash
ttt -m openrouter/google/gemini-flash-1.5 "prompt"
ttt --model claude-3-5-sonnet-20241022 "prompt"
```

**Proposed:**
```bash
ttt @claude "prompt"
ttt @gpt4 "prompt"
ttt @gemini "prompt"
ttt @local "prompt"
```

**Implementation:**
- Minimal: Just add model alias resolution in CLI
- Update config.yaml with alias mappings
- Effort: Low (1-2 hours)

### 2. Subcommand Structure

**Current:**
```bash
ttt --chat
ttt --status
ttt --models
ttt --config
```

**Proposed:**
```bash
ttt chat
ttt status
ttt models
ttt config
```

**Implementation:**
- Major refactor of cli.py to use Click command groups
- Breaking change requiring migration guide
- Effort: High (1-2 days)

### 3. Chat Session Management

**Current:**
```bash
ttt --chat  # No persistence, no resume
```

**Proposed:**
```bash
ttt chat                    # New session
ttt chat --resume           # Continue last
ttt chat --id meeting       # Named session
ttt chat --list             # Show all sessions
```

**Implementation:**
- Add SQLite or JSON file storage for sessions
- Implement session CRUD operations
- Update chat.py with persistence logic
- Effort: Medium (4-6 hours)

### 4. Configuration Management

**Current:**
```bash
# Edit config.yaml manually
# Use environment variables
```

**Proposed:**
```bash
ttt config                       # Show current
ttt config set model @claude     # Set default model
ttt config set temperature 0.7   # Set temperature
ttt config reset                 # Reset to defaults
```

**Implementation:**
- Add write-back capability to config system
- Handle config file updates safely
- Add config subcommands
- Effort: Medium (3-4 hours)

### 5. Simplified Tool Selection

**Current:**
```bash
ttt --tools TEXT "prompt"  # Unclear what TEXT should be
```

**Proposed:**
```bash
ttt --tools "prompt"              # Enable all tools
ttt --tools web,code "prompt"     # Enable specific tools
```

**Implementation:**
- Parse comma-separated tool list
- Update help text
- Effort: Low (30 minutes)

## Implementation Phases

### Phase 1: Quick Wins (1 day)
- Model shortcuts (@claude syntax)
- Simplified --tools flag
- Fix output modes (already completed)

### Phase 2: Subcommands (2-3 days)
- Refactor to command structure
- Maintain backward compatibility with deprecation warnings
- Update all tests

### Phase 3: Advanced Features (1 week)
- Chat session management
- Configuration management
- Pipe mode optimization
- Upgrade command

## Backward Compatibility

### Deprecation Strategy
```bash
# Old command shows warning:
$ ttt --chat
Warning: --chat is deprecated. Use 'ttt chat' instead.
[continues to work]

# After 3 months, remove old syntax
```

### Migration Guide
- Provide clear documentation
- Automated migration script for common patterns
- Keep both syntaxes working during transition

## Alternative: Minimal Changes

If full redesign is too disruptive, consider only:

1. **Add model shortcuts** without changing flags:
   ```bash
   ttt -m @claude "prompt"  # Just recognize @ prefix
   ```

2. **Add config commands** as flags:
   ```bash
   ttt --config-set model=@claude
   ```

3. **Enhance existing chat**:
   ```bash
   ttt --chat --resume
   ttt --chat --session meeting
   ```

## Metrics for Success

- Reduced time to first successful command for new users
- Fewer help/documentation lookups
- Increased usage of advanced features (chat sessions, config)
- Positive user feedback on usability

## Risks

1. **Breaking Changes**: May frustrate existing users
   - Mitigation: Careful deprecation period
   
2. **Complexity**: Subcommands add complexity
   - Mitigation: Excellent help text and examples
   
3. **Maintenance**: More code to maintain
   - Mitigation: Good test coverage

## Recommendation

Start with Phase 1 (model shortcuts, tool simplification) as these provide immediate value with minimal disruption. Evaluate user feedback before proceeding with more dramatic changes.

The full redesign would create a more professional, scalable CLI, but the minimal approach maintains stability while still improving usability.

## Next Steps

1. Gather team/user feedback on this proposal
2. Decide between full redesign vs minimal changes
3. Create detailed implementation plan for chosen approach
4. Begin with Phase 1 quick wins regardless of decision