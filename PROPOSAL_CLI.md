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

**Testing Strategy:**
- Run real CLI commands: `ttt @claude "What is 2+2?"` 
- Verify actual API calls work with shortcuts
- Test all model aliases against real providers
- NO MOCKS - skip tests if API keys unavailable

**Cleanup Checklist:**
- Remove old model string examples from all docs
- Update --help text to show @model syntax
- Delete any temporary alias parsing code
- Ensure no references to old long model strings

**Phase Gate:**
- All shortcuts work with real APIs
- Zero references to old syntax in codebase
- Documentation fully updated

### Phase 2: Subcommands (2-3 days)
- Refactor to command structure
- Implement parallel old/new syntax
- Full test suite migration

**Testing Strategy:**
- Real end-to-end tests: both syntaxes must work
  ```bash
  ttt --chat  # old
  ttt chat    # new
  ```
- Test with actual user sessions
- Verify real API calls through both paths
- Test with real files/pipes: `cat file.txt | ttt`

**Cleanup Checklist:**
- Remove ALL old flag handling code
- Delete deprecated argument parsers
- Update every example in docs to new syntax
- Remove old syntax from test files
- Search codebase for "--" patterns and eliminate

**Phase Gate:**
- Old syntax shows deprecation but works
- New syntax is primary in all docs
- No duplicate code paths

### Phase 3: Advanced Features (1 week)
- Chat session management
- Configuration management
- Pipe mode optimization

**Testing Strategy:**
- Create real chat sessions with actual APIs
- Test session persistence with real conversations
- Verify config changes with real API calls
- Test real multi-turn conversations:
  ```bash
  ttt chat --id project
  # Have real conversation
  ttt chat --resume project
  # Verify context maintained
  ```

**Cleanup Checklist:**
- Remove ALL deprecation warnings
- Delete backward compatibility layer
- Remove old flag definitions completely
- Clean up old config handling
- Ensure single source of truth for each feature

**Phase Gate:**
- Zero legacy code remains
- All tests use new syntax only
- No references to old patterns anywhere

## Testing Philosophy

### No Mocks, Only Real Tests
- If it can't be tested with real API calls, don't test it
- Skip tests when API keys are missing rather than mock
- Every test must exercise actual functionality
- Integration tests are the primary validation

### Test Organization
```bash
tests/
  phase1/           # Only new syntax tests
  phase2/           # Subcommand tests
  phase3/           # Advanced feature tests
  legacy/           # Deleted after each phase
```

## Backward Compatibility

### Strict Deprecation Timeline
```bash
# Phase 2: Show warning but work
$ ttt --chat
Warning: --chat is deprecated. Use 'ttt chat' instead.

# Phase 3: Remove completely
$ ttt --chat
Error: Unknown option '--chat'. Use 'ttt chat' instead.
```

### Migration Rules
- Each phase MUST delete its deprecated code
- No "just in case" legacy code retention
- Documentation shows ONLY current syntax
- Old examples = bugs to be fixed

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

## Cleanup Verification

### Automated Checks
```bash
# Run after each phase
./verify_cleanup.sh

# Checks for:
grep -r "--chat" .  # Should find ZERO matches after Phase 3
grep -r "openrouter/google/" docs/  # Should find ZERO after Phase 1
find . -name "*.deprecated.*"  # Should be empty
```

### Manual Review Checklist
- [ ] Help text shows only current syntax
- [ ] README has zero old examples  
- [ ] No commented-out legacy code
- [ ] Test files use only new patterns
- [ ] CI/CD configs updated
- [ ] No "backwards compatibility" imports

### Definition of Done
Each phase is ONLY complete when:
1. All real tests pass (no mocks)
2. Zero legacy code remains
3. Documentation is 100% current
4. Cleanup verification passes

## Next Steps

1. Gather team/user feedback on this proposal
2. Decide between full redesign vs minimal changes
3. Create detailed implementation plan for chosen approach
4. Begin with Phase 1 quick wins regardless of decision