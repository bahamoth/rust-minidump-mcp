# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python MCP (Model Context Protocol) server that provides minidump crash analysis capabilities. The project uses FastMCP to create both server and client interfaces for analyzing Windows crash dump files using Rust-based tools.

## Development Commands

### Environment Setup
```bash
uv venv              # Create virtual environment
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
# Using uvx (no installation required) - from project directory
uvx --from . minidump-mcp server
uvx --from . minidump-mcp server --transport streamable-http --port 8000
uvx --from . minidump-mcp server --transport sse --port 9000

# Traditional method (after uv sync)
minidump-mcp server
minidump-mcp server --transport streamable-http --port 8000
minidump-mcp server --transport sse --port 9000
```

### Running the Client
```bash
# Using uvx (no installation required) - from project directory
uvx --from . minidump-mcp client

# Traditional method (after uv sync)
minidump-mcp client  # Test client that connects to server and demos tools
```

Note: After PyPI deployment, the uvx commands will simplify to `uvx minidump-mcp server` and `uvx minidump-mcp client`.

## Architecture

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