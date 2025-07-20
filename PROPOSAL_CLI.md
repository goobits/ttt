# PROPOSAL_CLI.md - TTT CLI Redesign

## Executive Summary

This proposal outlines a redesign of the TTT CLI to improve usability while maintaining power. The goal is to create a more intuitive, discoverable API that scales from simple use cases to advanced workflows, implemented as a single, decisive upgrade.

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

### 1. Model Selection Shortcuts & Aliases

**Current:**
```bash
ttt -m openrouter/google/gemini-flash-1.5 "prompt"
```

**Proposed:**
```bash
# Built-in shortcuts
ttt @claude "prompt"
ttt @gpt4 "prompt"

# User-defined aliases
ttt @work-model "prompt" 
```

**Implementation:**
- Add model alias resolution in the CLI.
- Update `config.yaml` with a default alias map.
- Allow users to define custom aliases via the `ttt config set` command.
- Effort: Low (2-3 hours)

### 2. Subcommand Structure

**Current:**
```bash
ttt --chat
ttt --status
ttt --models
```

**Proposed:**
```bash
ttt chat
ttt status
ttt models
ttt config
```

**Implementation:**
- Refactor `cli.py` to use Click command groups.
- This is a **breaking change**. All old flag-based commands will be removed.
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
- Add SQLite or JSON file storage for sessions.
- Implement session CRUD operations.
- Update `chat.py` with persistence logic.
- Effort: Medium (4-6 hours)

### 4. Configuration Management

**Current:**
```bash
# Edit config.yaml manually or use environment variables
```

**Proposed:**
```bash
ttt config                       # Show current
ttt config set model @claude     # Set default model
ttt config set alias.work-model gpt-4-turbo # Set a custom alias
ttt config reset                 # Reset to defaults
```

**Implementation:**
- Add write-back capability to the config system.
- Handle config file updates safely.
- Add config subcommands.
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
- Parse comma-separated tool list.
- Update help text.
- Effort: Low (30 minutes)

## Implementation Plan

This will be a single, focused effort to migrate to the new design.

### Step 1: Foundational Changes (2-3 days)
- **Implement Subcommand Structure:** Refactor the CLI to use `click` subcommands. All old flags (`--chat`, `--status`, etc.) will be removed immediately.
- **Model Shortcuts & Aliases:** Implement the `@model` syntax and the `ttt config set alias...` functionality.
- **Simplified Tools Flag:** Implement the new comma-separated `--tools` flag.

### Step 2: Advanced Features (1 week)
- **Chat Session Management:** Build the persistence layer for chat sessions.
- **Configuration Management:** Implement the `ttt config` commands for writing to the config file.
- **Pipe Mode Optimization:** Ensure pipes work seamlessly with the new subcommands.

## Testing Philosophy

### Prefer Real Backends, Use Mocks Judiciously
- **Primary Goal:** Test against real API endpoints to ensure true functionality. Tests should be skipped gracefully if API keys are not available.
- **Acceptable Mocks:** For unit tests and offline development, it is acceptable to use mock backends that conform to the real backend interface, such as the existing `examples/plugins/mock_llm_backend.py`.
- **Discouraged Mocks:** Avoid mocking the network layer (e.g., patching `requests` or `httpx`). This is brittle and doesn't accurately reflect the backend integration.

### Test Organization
Tests will be organized by feature to create a clear and maintainable structure. The temporary phase-based folders will not be used.
```bash
tests/
  test_cli_chat.py      # Tests for 'ttt chat' subcommand
  test_cli_config.py    # Tests for 'ttt config' subcommand
  test_aliases.py       # Tests for model alias resolution
  ...etc
```

## Backward Compatibility

There will be **no backward compatibility**. This is a clean break from the old CLI syntax.

- All flag-based commands (`--chat`, `--status`) will be removed and replaced with subcommands.
- A clear section in the README and migration guide will explain the changes to users.
- This avoids technical debt and ensures a consistent, modern user experience from the start.

## Risks

1. **Breaking Changes**: Will require users to adapt.
   - **Mitigation**: Clear communication and documentation. A one-time, well-documented change is better than a lengthy, confusing deprecation period.
   
2. **Implementation Scope**: This is a significant, coordinated effort.
   - **Mitigation**: The focused, all-at-once approach prevents complexity from spreading across multiple phases.

## Cleanup Verification

### Automated Checks
A verification script will ensure no legacy code remains.
```bash
# ./verify_cleanup.sh

# Checks for:
grep -rE -- "--chat|--status|--models" . # Should find ZERO matches
grep -r "openrouter/google/" docs/      # Should find ZERO after implementation
```

### Manual Review Checklist
- [ ] Help text shows only new subcommand syntax.
- [ ] README and all documentation use only new examples.
- [ ] No commented-out legacy code exists.
- [ ] Test files use only the new subcommand patterns.

### Definition of Done
The project is complete when:
1. All tests pass against both real and mock backends.
2. Zero legacy CLI code or documentation remains.
3. The cleanup verification script passes.

## Next Steps

1. Gather final feedback on this revised, decisive proposal.
2. Create detailed implementation tickets for each part of the plan.
3. Begin implementation.