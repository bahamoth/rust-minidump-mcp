# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python MCP (Model Context Protocol) server that provides minidump crash analysis capabilities. The project uses FastMCP to create both server and client interfaces for analyzing Windows/macOS/Linux crash dump files using Rust-based tools.

**Key Features:**
- Cross-platform minidump analysis using Mozilla's rust-minidump tools
- Multiple transport support (streamable-http, stdio, sse)
- AI-assisted crash analysis with structured prompts
- Symbol resolution for better stack traces

## Development Commands

### Environment Setup
```bash
uv venv              # Create virtual environment (Python 3.13+)
uv sync              # Install dependencies from uv.lock
cp .env.example .env # Copy environment config template
```

### Install Rust Tools
```bash
just install-tools   # Downloads and installs platform-specific minidump-stackwalk and dump_syms to minidumpmcp/tools/bin/
```

### Code Quality
```bash
ruff check           # Lint code
ruff format          # Format code  
mypy .               # Type checking
pytest               # Run all tests
pytest tests/test_stackwalk.py -v  # Run specific test file with verbose output
```

### Running the Server
```bash
# HTTP transport (default)
minidump-mcp server  # Defaults to streamable-http on port 6543

# STDIO transport
minidump-mcp server --transport stdio

# SSE transport  
minidump-mcp server --transport sse --port 9000

# Custom port
minidump-mcp server --port 8080
```

### Running the Client
```bash
minidump-mcp client  # Interactive test client that demonstrates all available tools
```

## Architecture

### Project Structure
```
rust-minidump-mcp/
├── minidumpmcp/              # Main package
│   ├── __init__.py
│   ├── cli.py                # Typer-based CLI entry point
│   ├── server.py             # FastMCP server implementation
│   ├── config/               # Configuration module
│   │   ├── __init__.py
│   │   └── settings.py       # Pydantic settings with env var support
│   ├── tools/                # Tool implementations
│   │   ├── __init__.py
│   │   ├── stackwalk.py      # Minidump analysis tool provider
│   │   └── bin/              # Platform-specific Rust binaries
│   ├── prompts/              # AI prompt providers
│   │   ├── __init__.py
│   │   └── crash_analysis.py # Structured crash analysis prompts
│   └── resources/            # Future resource providers
├── tests/                    # Test suite
│   ├── test_settings.py      # Configuration tests
│   ├── test_stackwalk.py     # Tool functionality tests
│   └── testdata/             # Sample minidumps and symbols
├── docs/                     # Documentation
├── dist/                     # Build artifacts
├── symbols/                  # Converted symbol files
├── .env.example              # Environment configuration template
├── justfile                  # Task runner for tool installation
├── pyproject.toml            # Project metadata and dependencies
└── uv.lock                   # Locked dependencies

```

### Core Components

- **CLI (`cli.py`)**: Entry point providing `server` and `client` commands via Typer
- **Server (`server.py`)**: FastMCP server that registers tools and prompts, supports multiple transports
- **Configuration (`config/settings.py`)**: Pydantic Settings for all transport types with `.env` support
- **Stackwalk Tool (`tools/stackwalk.py`)**: Wraps rust-minidump tools for crash analysis
- **Crash Analysis Prompts (`prompts/crash_analysis.py`)**: Structured prompts for AI-assisted debugging

### Tool Integration

The project uses Mozilla's rust-minidump tools:
- **minidump-stackwalk**: Analyzes minidump files and produces stack traces
- **dump_syms**: Converts PDB/DWARF symbols to Breakpad format

Platform-specific binaries are stored in `minidumpmcp/tools/bin/` with suffixes like `-macos`, `-linux`, `-windows.exe`. The `justfile` automates downloading and installing the correct versions.

### Transport Support

FastMCP server supports three transport types:
- **streamable-http**: HTTP-based transport (default, port 6543)
- **stdio**: Standard input/output 
- **sse**: Server-Sent Events transport

Configuration uses environment variables with the pattern:
- `MINIDUMP_MCP_TRANSPORT`: Transport type
- `MINIDUMP_MCP_HTTP__PORT`: HTTP server port
- `MINIDUMP_MCP_SSE__PORT`: SSE server port

### Testing

- **Test Data**: `tests/testdata/` contains sample minidump files and symbol directories
- **Coverage**: Tests validate tool execution, configuration loading, and error handling
- **CI/CD**: GitHub Actions workflow runs linting, type checking, and tests on push

## MCP Tools Available

### analyze_minidump
Analyzes a minidump crash file and returns detailed stack trace information.

**Parameters:**
- `minidump_path` (str, required): Path to the minidump file
- `symbols_path` (str, optional): Path to symbols directory
- `output_format` (str, optional): Output format - "human" (default) or "json"

**Example Usage:**
```python
result = await analyze_minidump(
    minidump_path="crash.dmp",
    symbols_path="./symbols",
    output_format="json"
)
```

### extract_symbols
Extracts Breakpad symbols from binary files (PDB, DWARF, etc.) using dump_syms.

**Parameters:**
- `binary_path` (str, required): Path to the binary file to extract symbols from
- `output_dir` (str, optional): Directory to save the symbol file (default: ./symbols/)

**Returns:**
Dictionary containing:
- `success`: Whether the operation succeeded
- `symbol_file`: Path to the generated symbol file
- `module_info`: Information about the module (name, id, os, arch)
- `error`: Error message if failed

**Example Usage:**
```python
result = await extract_symbols(
    binary_path="/path/to/app.exe",
    output_dir="./symbols"
)

if result["success"]:
    print(f"Symbols saved to: {result['symbol_file']}")
    print(f"Module: {result['module_info']['name']} ({result['module_info']['id']})")
```

## MCP Prompts Available

### crash_analysis
Provides structured guidance for analyzing crash dumps with relevant context about crash patterns, debugging strategies, and common issues.

## Common Tasks

### Adding Symbol Support
1. Place PDB or DWARF files in a directory
2. Use the `extract_symbols` tool to convert them to Breakpad format:
   ```python
   result = await extract_symbols(binary_path="myapp.pdb")
   ```
3. The tool automatically organizes symbols in the Breakpad directory structure: `<module>/<id>/<module>.sym`
4. Pass the symbols directory path to `analyze_minidump`

### Debugging Crashes
1. Obtain the minidump file from the crash
2. Gather relevant symbol files (PDBs, DWARFs)
3. Use the `analyze_minidump` tool to get the stack trace
4. Use the `crash_analysis` prompt for AI assistance in interpreting results

### Extending the Server
1. Add new tools in `minidumpmcp/tools/`
2. Add new prompts in `minidumpmcp/prompts/`
3. Register them in `server.py`
4. Update tests and documentation