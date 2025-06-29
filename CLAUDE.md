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

### Running the Server
```bash
# Development - from project directory
python -m minidumpmcp server                    # Default: Streamable HTTP on port 8000
python -m minidumpmcp server --transport stdio  # For AI agent integration
python -m minidumpmcp server --transport sse --port 9000

# Using uvx (from project directory during development)
uvx --from . rust-minidump-mcp server                    # Default: Streamable HTTP on port 8000
uvx --from . rust-minidump-mcp server --transport stdio  # For AI agent integration
uvx --from . rust-minidump-mcp server --transport sse --port 9000

# Traditional method (after uv sync)
rust-minidump-mcp server                                  # Default: Streamable HTTP on port 8000
rust-minidump-mcp server --transport streamable-http --port 8080  # Custom port
rust-minidump-mcp server --transport stdio                # For AI agent integration
rust-minidump-mcp server --transport sse --port 9000      # Server-Sent Events
```

### Running the Client
```bash
# Development - from project directory
python -m minidumpmcp client

# Using uvx (from project directory during development)
uvx --from . rust-minidump-mcp client

# Traditional method (after uv sync)
rust-minidump-mcp client  # Test client that connects to server and demos tools
```

Note: After PyPI deployment, the uvx commands will simplify to `uvx rust-minidump-mcp server` and `uvx rust-minidump-mcp client`.

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
- **stdio**: Standard input/output (default)
- **streamable-http**: HTTP-based transport 
- **sse**: Server-Sent Events transport

Configuration is handled through Pydantic Settings with environment variable overrides using the pattern `MINIDUMP_MCP_<SETTING>__<NESTED_SETTING>`.

### Testing

Test data is in `tests/testdata/` including sample minidump files and symbol directories. The test suite validates both the stackwalk tool execution and configuration loading.