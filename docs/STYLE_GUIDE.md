# Documentation Style Guide

This guide ensures consistency across all Goobits TTT documentation. Follow these principles when writing or updating docs.

## Core Principles

### 1. **Concise but Complete**
- Maximum information density with minimum word count
- Every sentence must serve a purpose
- Cut fluff, keep clarity
- Prefer bullet points over paragraphs

**Good**: "Set API keys via environment variables or config files."
**Bad**: "There are multiple different ways that you can go about setting up your API keys, and one of the most common approaches is to use environment variables, although you can also use config files if you prefer."

### 2. **Action-Oriented**
- Start with verbs when giving instructions
- Focus on what users should do, not what exists
- Use imperative mood for steps

**Good**: "Run `./run-tests.sh` to execute tests."
**Bad**: "Tests can be run by executing the test script."

### 3. **User-First Perspective**
- Address reader as "you"
- Focus on user benefits and goals
- Lead with the "why" or value proposition
- Assume intelligence but not knowledge

**Good**: "You can stream responses to see output as it's generated."
**Bad**: "The library provides a streaming capability for responses."

### 4. **Technical Accuracy**
- All code examples must be tested and work
- File paths must match actual structure
- Function signatures must be current
- Links must resolve correctly
- Version-specific info must be marked

### 5. **Consistent Terminology**
- **First mention**: "Goobits TTT"
- **Subsequent mentions**: "TTT"
- **Never**: "the AI library", "the system", "this tool" (too vague)
- See [GLOSSARY.md](./GLOSSARY.md) for term definitions

### 6. **Approachable but Professional**
- Friendly tone without being chatty
- Technical without being dense
- Confident without being arrogant
- Helpful without being condescending

## Writing Style

### Voice & Tone
- **Active voice**: "TTT routes requests" not "Requests are routed by TTT"
- **Present tense**: "Returns an AIResponse" not "Will return an AIResponse"
- **Direct**: "Use `ask()` for simple requests" not "You might want to consider using..."

### Sentence Structure
- **Max 20 words per sentence** (aim for 12-15)
- **One idea per sentence**
- **Vary sentence length** for readability
- **Break complex ideas** into multiple sentences

### Paragraphs
- **Max 4-5 sentences** per paragraph
- **One topic** per paragraph
- **Use bullet lists** when listing 3+ items
- **Add whitespace** between sections

## Formatting Conventions

### Headings
```markdown
# Document Title (H1 - once per document)

## Major Section (H2)

### Subsection (H3)

#### Minor Point (H4 - rarely needed)
```

- Use sentence case, not title case
- Be descriptive: "Setting up API keys" not "Setup"
- Avoid generic headings: "Overview", "Introduction"

### Code Examples
- **Include context**: What the code does and why
- **Use real examples**: Actual model names, realistic prompts
- **Show output**: When helpful for understanding
- **Add comments**: Only for non-obvious logic

```python
# Good example
from ttt import ask

# Get weather info using function calling
response = ask(
    "What's the weather in Tokyo?",
    model="gpt-4",
    tools=[get_weather]  # Custom weather tool
)
```

### Lists
- Use **bullets** for unordered items
- Use **numbers** only for sequential steps
- Use **checkboxes** for task lists
- Keep items parallel in structure

### Links
- **Descriptive text**: "See [Configuration Guide](./configuration.md)"
- **Not**: "Click [here](./configuration.md) for more info"
- **Verify all links** work before committing

### Emphasis
- **Bold**: Key terms on first use, important warnings
- *Italic*: Minimal use - only for specific emphasis
- `Code`: Functions, file names, commands, parameters
- > Blockquote: Important notes, warnings, tips

## Content Structure

### Document Template
```markdown
# Document Title

Brief (1-2 sentence) description of what this document covers.

## Prerequisites (if applicable)
What you should know/read before this document.

## Quick Start / Overview
The essential 20% that delivers 80% of value.

## Main Content
Organized by task or concept, most important first.

## Advanced Topics (if applicable)
Power user features, edge cases, deep dives.

## Related Resources
Links to other relevant documentation.
```

### Code Reference Format
```markdown
### `function_name()`

Brief one-line description.

**Parameters:**
- `param1` (type): Description
- `param2` (type, optional): Description. Default: value

**Returns:**
- `ReturnType`: Description of return value

**Example:**
```python
result = function_name(param1="value")
```
```

## Naming Conventions

### Project Names
- **Package**: `goobits-ttt` (PyPI package name)
- **Command**: `ttt` (CLI command)
- **Python module**: `ttt` (import name)
- **Full name**: Goobits TTT (marketing, README)
- **Short name**: TTT (docs, after first mention)

### Files
- Use kebab-case: `api-reference.md`, `getting-started.md`
- Be descriptive: `configuration.md` not `config.md`
- Avoid abbreviations unless very common

### Code
- Follow Python PEP 8 conventions
- Use descriptive names in examples
- Avoid `foo`, `bar` - use domain-appropriate names

## Common Patterns

### Prerequisites Section
```markdown
## Prerequisites

**Required knowledge:**
- Basic Python programming
- Familiarity with async/await (for async APIs)

**Required reading:**
- [Configuration Guide](./configuration.md) - API key setup
```

### Installation Instructions
```markdown
Install via pip:
```bash
pip install goobits-ttt
```

Verify installation:
```bash
ttt --version
```
```

### Configuration Examples
Always show both environment variable and config file approaches:

```markdown
Set your API key:

**Via environment variable:**
```bash
export OPENAI_API_KEY="sk-..."
```

**Via config file** (`~/.config/ttt/config.yaml`):
```yaml
api_keys:
  openai: "sk-..."
```
```

## Review Checklist

Before committing documentation:

- [ ] All code examples tested and working
- [ ] All links verified (internal and external)
- [ ] File paths match actual structure
- [ ] Terminology consistent (see GLOSSARY.md)
- [ ] No spelling or grammar errors
- [ ] Follows active voice and present tense
- [ ] Sentences under 20 words
- [ ] Project naming consistent (Goobits TTT → TTT)
- [ ] Formatted correctly (headings, code blocks, lists)
- [ ] Cross-references to related docs included

## Examples

### Before vs After

**Before (verbose, passive, generic):**
```markdown
## Introduction

This section will provide you with information about how the configuration
system works. There are several different ways that configuration can be
provided to the system, and they are applied in a specific order.
```

**After (concise, active, specific):**
```markdown
## Configuration System

TTT loads configuration from multiple sources in order of precedence:
1. Direct parameters (highest priority)
2. Environment variables
3. Config files (`ai.yaml`)
4. Default values
```

---

**Maintained by**: TTT Documentation Team
**Last Updated**: 2025-01-10
**Questions?**: Open an issue on GitHub
