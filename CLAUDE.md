# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**IMPORTANT**: Always read TASKS.md first before starting any work. Check TASKS.md for the current development phase and continue from the next uncompleted task.

## Working Process

1. **Start by reading TASKS.md** to understand:
   - Current development phase
   - Completed tasks (marked with [x])
   - Next pending tasks (marked with [ ])
   - Overall project roadmap

2. **Continue work** from the next uncompleted task in TASKS.md

3. **Update TASKS.md** as you complete tasks

## Important References

- **TASKS.md**: Current development tasks and roadmap for PyPI publishing. This file contains the active work items and must be consulted before any development work.

## Project Overview

This is a Python MCP (Model Context Protocol) server that provides minidump crash analysis capabilities. The project uses FastMCP to create both server and client interfaces for analyzing Windows crash dump files using Rust-based tools.

## Development Commands

### Environment Setup
```bash
uv sync              # Install dependencies
```

### Install Rust Tools
```bash
just install-tools   # Installs minidump-stackwalk and dump_syms to minidumpmcp/tools/bin/
```

### Code Quality
```bash
ruff check           # Lint code
ruff format          # Format code  
mypy .               # Type checking
pytest               # Run tests
pytest tests/test_stackwalk.py  # Run specific test file
```

## Code Quality Checks

**IMPORTANT**: After completing any implementation task, you MUST automatically run the following commands in this exact order:

1. `ruff check --fix` - Fix linting issues automatically
2. `ruff format` - Format code (Black-compatible formatting)
3. `mypy .` - Run type checking

If any of these commands fail:
- Fix the issues reported
- Re-run all commands until they pass
- Only consider the task complete when all checks pass

Do NOT ask the user for permission to run these checks - they are mandatory after any code changes.

## Task Completion Checklist

Before marking any coding task as complete, you MUST:

- [ ] Run `ruff check --fix` and fix any remaining issues
- [ ] Run `ruff format` to ensure consistent formatting  
- [ ] Run `mypy .` and fix all type errors
- [ ] Verify tests still pass with `pytest` (if tests exist for the changed code)
- [ ] Confirm no new warnings or errors were introduced

This checklist is non-negotiable and must be completed for EVERY code change.

## Development Workflow

When implementing features or fixing bugs:

1. Write/modify code
2. Immediately run quality checks:
   ```bash
   ruff check --fix && ruff format && mypy .
   ```
3. If any command fails, fix issues and repeat step 2
4. Only proceed to next task after all checks pass

Example workflow:
- User: "Add a new feature X"
- Claude: *implements feature* → *runs checks* → *fixes issues* → *confirms completion*

### Running the Server
```bash
# Development - from project directory
python -m minidumpmcp server                    # Default: stdio transport
python -m minidumpmcp server --transport streamable-http --port 8000  # For web access
python -m minidumpmcp server --transport sse --port 9000

# Using uvx (recommended - no installation needed)
uvx rust-minidump-mcp server                              # Default: stdio transport
uvx rust-minidump-mcp server --transport streamable-http  # For web access
uvx rust-minidump-mcp server --transport sse --port 9000  # Server-Sent Events

# Traditional method (after pip/uv install)
rust-minidump-mcp server                                  # Default: stdio transport
rust-minidump-mcp server --transport streamable-http --port 8080  # For web access
rust-minidump-mcp server --transport sse --port 9000      # Server-Sent Events
```

### Running the Client
```bash
# Development - from project directory
python -m minidumpmcp client

# Using uvx (recommended - no installation needed)
uvx rust-minidump-mcp client

# Traditional method (after pip/uv install)
rust-minidump-mcp client  # Test client that connects to server and demos tools
```

## Architecture

For ongoing PyPI publishing and release management tasks, refer to TASKS.md Phase 2-5.

### Core Components

- **minidumpmcp/server.py**: FastMCP server entry point that registers tools and prompts
- **minidumpmcp/cli.py**: Typer-based CLI with server/client commands
- **minidumpmcp/config/settings.py**: Pydantic-based configuration with environment variable support
- **minidumpmcp/tools/stackwalk.py**: Main tool provider for minidump analysis using Rust binaries
- **minidumpmcp/tools/dump_syms.py**: Tool for extracting Breakpad symbols from binaries
- **minidumpmcp/prompts/**: Crash analysis prompt providers for AI-assisted debugging

### Tool Integration

The project packages pre-compiled Rust binaries (`minidump-stackwalk`, `dump_syms`) in `minidumpmcp/tools/bin/` with platform-specific naming (e.g., `minidump-stackwalk-macos`). The justfile handles cross-platform installation of these tools.

### MCP Tools

#### stackwalk_minidump
Analyzes minidump crash files to produce human-readable stack traces.

**Parameters:**
- `minidump_path` (str, required): Path to the minidump file
- `symbols_path` (str, optional): Path to symbol files or directories
- `verbose` (bool, optional): Include verbose output (default: False)

**Returns:**
- Stack traces with function names, file paths, and line numbers
- Thread information and crash reason
- Module list and system info

#### extract_symbols
Extracts Breakpad symbol files from binary files (PDB, DWARF) using the `dump_syms` tool.

**Parameters:**
- `binary_path` (str, required): Path to the binary file
- `output_dir` (str, optional): Directory to save symbols (default: ./symbols/)

**Returns:**
- `success` (bool): Operation status
- `symbol_file` (str): Path to generated .sym file
- `module_info` (dict): Module name, ID, OS, and architecture
- `error` (str): Error message if failed

**Example:**
```python
result = await extract_symbols(
    binary_path="/path/to/app.exe",
    output_dir="./symbols"
)
# Creates: ./symbols/app.exe/1234ABCD/app.exe.sym
```

### Transport Support

FastMCP server supports three transport types:
- **stdio**: Standard input/output (default) - for AI agent integration
- **streamable-http**: HTTP-based transport - for web access and debugging
- **sse**: Server-Sent Events transport - for real-time streaming

Configuration is handled through Pydantic Settings with environment variable overrides using the pattern `MINIDUMP_MCP_<SETTING>__<NESTED_SETTING>`.

### MCP Prompts

The project provides three focused prompts for crash analysis:

- **analyze_crash_with_expertise**: Expert-level crash analysis with role-based insights
  - Detects programming language from modules/symbols
  - Provides concrete code improvement suggestions
  - Identifies crash patterns and prevention strategies
  - Offers tailored advice based on technology stack

- **analyze_technical_details**: Deep technical analysis of crash internals
  - Register state interpretation
  - Stack frame pattern analysis
  - Memory corruption detection
  - Symbol-less frame estimation techniques

- **symbol_transformation_guide**: Comprehensive guide for symbol preparation
  - Explains Breakpad format requirements
  - Documents dump_syms tool usage
  - Shows expected directory structure
  - Common troubleshooting tips

### Testing

Test data is in `tests/testdata/` including sample minidump files and symbol directories. The test suite validates both the stackwalk tool execution and configuration loading.