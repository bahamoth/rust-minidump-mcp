# Tools Directory - AI Agent Instructions

This directory is dedicated to installing Rust tools for minidump analysis using `cargo install`.

## Installed Tools

### 1. minidump-stackwalk
- **Purpose**: Analyzes crash dump files to generate stack traces
- **Features**: 
  - Reads minidump files (.dmp) to extract stack information at the time of crash
  - Provides function names and line number information using symbol files
  - Outputs detailed stack information for crash cause analysis

### 2. dump_syms
- **Purpose**: Extracts debug symbols from binary files
- **Features**:
  - Extracts symbol information from executables or libraries
  - Generates Breakpad format symbol files (.sym)
  - Provides symbol data that can be used by minidump-stackwalk

## Installation Method

Run the following command from the project root:

```bash
just install-tools
```

This command:
1. Creates the `tools` directory (if it doesn't exist)
2. Installs `minidump-stackwalk` to the `./tools` directory
3. Installs `dump_syms` to the `./tools` directory
4. The installed tools are located in the `tools/bin/` directory

## Usage Examples

### minidump-stackwalk Usage
```bash
./tools/bin/minidump-stackwalk /path/to/crash.dmp /path/to/symbols/
```

### dump_syms Usage
```bash
./tools/bin/dump_syms /path/to/binary > symbol_file.sym
```

## Key Information for AI Agents

- **Tool Location**: `tools/bin/` directory
- **Dependencies**: These tools are written in Rust and installed via cargo
- **Purpose**: Core tools for crash dump analysis workflow
- **Interaction**: Use dump_syms to generate symbols, then minidump-stackwalk to analyze dumps

These tools serve as the backend analysis engine for the minidump MCP server.