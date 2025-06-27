# Rust Minidump MCP

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A Python MCP (Model Context Protocol) server that provides minidump crash analysis capabilities. This project uses FastMCP to create both server and client interfaces for analyzing Windows crash dump files using Rust-based tools.

## 🚀 Features

- **Minidump Analysis**: Analyze Windows crash dump files (`.dmp`) to get detailed stack traces
- **Symbol Extraction**: Extract Breakpad symbols from binaries (PDB, DWARF formats)
- **Multiple Transports**: Support for stdio, HTTP, and SSE transports
- **AI-Powered Analysis**: Built-in prompts for AI-assisted crash debugging
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Comprehensive Error Handling**: Detailed error messages with actionable suggestions

## 📋 Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- [just](https://github.com/casey/just) command runner (optional)

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/bahamoth/rust-minidump-mcp.git
cd rust-minidump-mcp
```

### 2. Create virtual environment and install dependencies

```bash
uv venv
uv sync
```

### 3. Install Rust tools

The project includes pre-compiled Rust binaries. Install them using:

```bash
just install-tools
```

This installs:
- `minidump-stackwalk`: For analyzing minidump files
- `dump_syms`: For extracting Breakpad symbols

## 🚀 Quick Start

### Method 1: Using uvx (No Installation Required)

You can run the tool directly without installation using [uvx](https://github.com/astral-sh/uv):

```bash
# From the project directory
uvx --from . minidump-mcp server
uvx --from . minidump-mcp client

# After PyPI deployment (future)
uvx minidump-mcp server
uvx minidump-mcp client
```

### Method 2: Traditional Installation

After installation with `uv sync`, you can use the standard command:

### Running the Server

#### STDIO Transport (default)
```bash
minidump-mcp server
```

#### HTTP Transport
```bash
minidump-mcp server --transport streamable-http --port 8000
```

#### SSE Transport
```bash
minidump-mcp server --transport sse --port 9000
```

### Running the Client

```bash
# Connect using default settings
minidump-mcp client

# Connect to custom server
minidump-mcp client --url http://localhost:8080/mcp

# Use environment variables
export MINIDUMP_MCP_CLIENT_URL=http://localhost:8080/mcp
minidump-mcp client
```

## 📚 MCP Tools

### stackwalk_minidump

Analyzes minidump crash files to produce human-readable stack traces.

**Parameters:**
- `minidump_path` (str, required): Path to the minidump file
- `symbols_path` (str, optional): Path to symbol files or directories
- `verbose` (bool, optional): Include verbose output (default: False)

**Example:**
```python
result = await stackwalk_minidump(
    minidump_path="/path/to/crash.dmp",
    symbols_path="/path/to/symbols"
)
```

### extract_symbols

Extracts Breakpad symbol files from binary files (PDB, DWARF).

**Parameters:**
- `binary_path` (str, required): Path to the binary file
- `output_dir` (str, optional): Directory to save symbols (default: ./symbols/)

**Example:**
```python
result = await extract_symbols(
    binary_path="/path/to/app.exe",
    output_dir="./symbols"
)
# Creates: ./symbols/app.exe/1234ABCD/app.exe.sym
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
# Server configuration
MINIDUMP_MCP_NAME=my-minidump-server
MINIDUMP_MCP_LOG_LEVEL=INFO
MINIDUMP_MCP_TRANSPORT=streamable-http
MINIDUMP_MCP_STREAMABLE_HTTP__HOST=127.0.0.1
MINIDUMP_MCP_STREAMABLE_HTTP__PORT=8000

# Client configuration
MINIDUMP_MCP_CLIENT_URL=http://localhost:8000/mcp
MINIDUMP_MCP_CLIENT_TRANSPORT=streamable-http
MINIDUMP_MCP_CLIENT_TIMEOUT=30.0
```

### Configuration Priority

1. CLI arguments (highest priority)
2. Environment variables
3. `.env` file
4. Default values (lowest priority)

## 🏗️ Architecture

### Project Structure

```
rust-minidump-mcp/
├── minidumpmcp/
│   ├── __init__.py
│   ├── server.py          # FastMCP server entry point
│   ├── cli.py             # Typer-based CLI
│   ├── exceptions.py      # Custom error handling
│   ├── config/
│   │   ├── settings.py    # Server configuration
│   │   └── client_settings.py  # Client configuration
│   ├── tools/
│   │   ├── stackwalk.py   # Minidump analysis tool
│   │   ├── dump_syms.py   # Symbol extraction tool
│   │   └── bin/           # Platform-specific binaries
│   └── prompts/           # AI-assisted debugging prompts
├── tests/                 # Test suite
├── justfile              # Task automation
└── pyproject.toml        # Project configuration
```

### Transport Support

- **stdio**: Standard input/output for CLI integration
- **streamable-http**: HTTP-based transport for web services
- **sse**: Server-Sent Events for real-time streaming

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_stackwalk.py

# Run with coverage
pytest --cov=minidumpmcp
```

### Code Quality

```bash
# Lint code
ruff check

# Format code
ruff format

# Type checking
mypy .
```

### Available Commands

See all available commands:
```bash
just --list
```

Common commands:
- `just install-tools`: Install Rust binaries
- `just test`: Run tests
- `just lint`: Run linters
- `just format`: Format code

## 🐛 Troubleshooting

### Common Issues

1. **Binary not found error**
   ```
   Solution: Run 'just install-tools' to install required binaries
   ```

2. **Connection refused error**
   ```
   Solution: Ensure the server is running on the correct port
   Check: minidump-mcp server --transport streamable-http --port 8000
   ```

3. **Invalid minidump format**
   ```
   Solution: Ensure the file is a valid Windows minidump (.dmp) file
   ```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📊 Understanding Crash Analysis

### Minidump Files

Minidump files (`.dmp`) are compact crash reports generated when a Windows application crashes. They contain:
- Thread information and stack traces
- CPU register states
- Loaded module list
- Exception information
- System information

### Symbol Files

Symbol files map memory addresses to human-readable function names and source locations:
- **PDB files**: Windows debug symbols
- **DWARF**: Linux/macOS debug information
- **Breakpad format**: Cross-platform symbol format (`.sym`)

### Analysis Workflow

1. **Crash occurs**: Application generates a minidump
2. **Extract symbols**: Use `extract_symbols` on the crashed binary
3. **Analyze dump**: Use `stackwalk_minidump` with symbols
4. **Interpret results**: Get function names, file paths, and line numbers

Example workflow:
```bash
# 1. Extract symbols from your application
minidump-mcp extract-symbols /path/to/app.exe --output ./symbols

# 2. Analyze the crash dump
minidump-mcp analyze /path/to/crash.dmp --symbols ./symbols
```

## 📁 Symbol Directory Structure

Breakpad symbols follow a specific directory structure:
```
symbols/
└── app.exe/
    └── 1234ABCD5678EF90/  # Module ID
        └── app.exe.sym    # Symbol file
```

This structure allows the analyzer to automatically find the correct symbols for each module in the crash dump.

## 🔗 Related Projects

- [rust-minidump](https://github.com/rust-minidump/rust-minidump): The Rust library powering our analysis tools
- [FastMCP](https://github.com/jlowin/fastmcp): The MCP framework used for server/client implementation
- [Breakpad](https://chromium.googlesource.com/breakpad/breakpad/): The crash reporting system that defines the symbol format
