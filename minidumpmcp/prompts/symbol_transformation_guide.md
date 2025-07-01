# Symbol Transformation Guide

Guide for transforming native debug symbols (PDB, DWARF) to Breakpad format required by minidump analysis tools.

## Why Breakpad Format?

The `minidump-stackwalk` tool requires symbols in Breakpad text format (.sym files) because:
- **Cross-platform compatibility**: Single format works for Windows, Linux, and macOS crashes
- **Lightweight**: Text-based format is smaller than native PDB/DWARF files
- **Fast lookup**: Optimized for quick symbol resolution during stack walking
- **Standardized**: Consistent format across all platforms and architectures

## Using dump_syms Tool

The `extract_symbols` MCP tool uses `dump_syms` internally to convert symbols:

```python
# Convert PDB to Breakpad format
result = await extract_symbols(
    binary_path="/path/to/app.pdb",
    output_dir="./symbols"
)
```

### Input Formats
- **Windows**: PDB files (.pdb)
- **Linux**: ELF binaries with DWARF debug info
- **macOS**: dSYM bundles or Mach-O binaries with DWARF

## Expected Output Structure

After conversion, Breakpad symbols follow this directory structure:
```
symbols/
├── app.exe/
│   └── 5A9B4C7D8E6F2A1B3C4D5E6F7A8B9C0D/
│       └── app.exe.sym
├── module.dll/
│   └── 1234567890ABCDEF1234567890ABCDEF/
│       └── module.dll.sym
```

Each .sym file contains:
```
MODULE windows x86_64 5A9B4C7D8E6F2A1B3C4D5E6F7A8B9C0D app.exe
FILE 0 /src/main.cpp
FILE 1 /src/utils.cpp
FUNC 1000 4e 0 main
1000 10 42 0
1010 20 43 0
...
```

## Common Troubleshooting

### Missing Symbols in Stackwalk
**Symptom**: `<name omitted>` or raw addresses in stack traces
**Cause**: Symbols not found in expected location
**Fix**: Ensure symbol path matches MODULE ID from minidump

### Incomplete Symbol Files
**Symptom**: Some functions resolved but others missing
**Cause**: Stripped binaries or partial debug info
**Fix**: Use unstripped binaries or full PDB files for conversion

### Wrong Architecture
**Symptom**: Symbol loading fails completely
**Cause**: Mismatch between binary architecture and minidump
**Fix**: Use symbols from exact same build as crashed binary

## Automation Example

Add to your build pipeline:
```bash
# After building your application
dump_syms app.pdb > app.sym
# Create proper directory structure
MODULE_ID=$(head -1 app.sym | awk '{print $4}')
mkdir -p symbols/app.exe/$MODULE_ID
mv app.sym symbols/app.exe/$MODULE_ID/
```

