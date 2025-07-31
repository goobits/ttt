# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Information

**Package**: `goobits-ttt` (PyPI) | **Command**: `ttt` | **Version**: 1.0.0rc4 | **Python**: 3.8+

## Key Development Commands

### Quick Reference
- Use the virtual environment when running commands, not the global python (see README for setup details)
- `./test.sh` - Run unit tests (default, free, fast)
- `./test.sh integration` - Run integration tests (requires API keys, costs money)
- `ruff src/ttt/ tests/` - Run linter
- `black src/ttt/ tests/` - Format code
- `mypy src/ttt/` - Type checking
- `./setup.sh install --dev` - Development installation (RECOMMENDED)

## Important Development Notes

### Test Execution
**Always use `./test.sh` for tests** - DO NOT run `pytest` directly for integration tests as it bypasses critical rate limiting.

### Development Installation
Always use `./setup.sh install --dev` for development work. This creates an editable installation where code changes are immediately reflected without needing to reinstall.

### Code Style Guidelines
- Black formatting (line length: 88)
- Ruff linting (checks: E, W, F, I, B, C4, UP; ignores: E501, B008, C901)
- MyPy type checking (strict mode)
- Follow existing patterns in similar files

### Temporary Files
When creating temporary debug or test scripts, use `/tmp` directory to keep the project clean.

## Project-Specific Instructions

### CLI Generation
The project uses Goobits CLI framework: run `goobits build` to generate CLI and setup scripts from goobits.yaml configuration.

### Tool Development Guidelines
- Use `@tool` decorator from `src/ttt/tools/base.py`
- Include comprehensive docstrings for schema generation
- Test security implications for code execution tools
- Follow existing patterns in `src/ttt/tools/builtins.py`

### Key File Locations
- Main API: `src/ttt/api.py`
- CLI entry: `src/ttt/cli.py` and `src/ttt/__main__.py`
- Backends: `src/ttt/backends/`
- Tools: `src/ttt/tools/`
- Configuration: `src/ttt/config.py`, `config.yaml`

## Documentation References

For detailed information, refer to:
- **README.md** - Project overview and quick start
- **docs/configuration.md** - Configuration details
- **docs/development.md** - Development setup and contributing
- **docs/architecture.md** - System architecture
- **docs/api-reference.md** - API documentation
- **tests/README.md** - Testing guide
