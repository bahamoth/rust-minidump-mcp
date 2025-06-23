"""dump_syms tool provider for extracting symbols from binaries."""

import asyncio
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from ._common import ToolExecutionError, run_subprocess


def _get_dump_syms_path() -> Path:
    """Get the platform-specific dump_syms binary path."""
    prefix = Path(__file__).parent / "bin"
    match platform.system().lower():
        case "linux":
            return prefix / "dump-syms-linux"
        case "darwin":
            return prefix / "dump-syms-macos"
        case "windows":
            return prefix / "dump-syms-windows.exe"
        case _:
            # Try generic name as fallback
            generic_path = prefix / "dump_syms"
            if generic_path.exists():
                return generic_path
            raise ValueError(f"Unsupported platform: {platform.system()}")


class DumpSymsTool:
    """Tool for extracting Breakpad symbols from binaries using dump_syms."""

    async def extract_symbols(
        self,
        binary_path: str,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract symbols from a binary file using dump_syms.

        Args:
            binary_path: Path to the binary file (PDB, DWARF, etc.)
            output_dir: Directory to save the symbol file.
                       If not provided, symbols will be saved to ./symbols/

        Returns:
            Dictionary containing:
                - success: Whether the operation succeeded
                - symbol_file: Path to the generated symbol file
                - module_info: Information about the module (name, id, os, arch)
                - error: Error message if failed

        Raises:
            FileNotFoundError: If binary file doesn't exist
            RuntimeError: If dump_syms execution fails
        """
        try:
            binary_file = Path(binary_path).resolve()
            if not binary_file.exists():
                return {"success": False, "error": f"Binary file not found: {binary_file}"}

            # Set output directory
            if output_dir:
                output_path = Path(output_dir).resolve()
            else:
                output_path = Path.cwd() / "symbols"

            output_path.mkdir(parents=True, exist_ok=True)

            # Get dump_syms binary
            dump_syms = _get_dump_syms_path()
            if not dump_syms.exists():
                return {
                    "success": False,
                    "error": f"dump_syms binary not found at {dump_syms}. Run 'just install-tools' to install it.",
                }

            # Run dump_syms to extract symbols
            cmd = [str(dump_syms), str(binary_file)]
            stdout = await run_subprocess(cmd)

            # Parse the symbol data
            if not stdout:
                return {"success": False, "error": "dump_syms produced no output"}

            # Extract module info from first line
            # Format: MODULE <os> <arch> <id> <name>
            first_line = stdout.split("\n")[0]
            parts = first_line.split()

            if len(parts) < 5 or parts[0] != "MODULE":
                return {"success": False, "error": f"Invalid symbol header: {first_line}"}

            module_os = parts[1]
            module_arch = parts[2]
            module_id = parts[3]
            module_name = parts[4]

            # Create Breakpad directory structure: <module>/<id>/<module>.sym
            symbol_dir = output_path / module_name / module_id
            symbol_dir.mkdir(parents=True, exist_ok=True)

            symbol_file = symbol_dir / f"{module_name}.sym"

            # Write symbol content
            symbol_file.write_text(stdout)

            return {
                "success": True,
                "symbol_file": str(symbol_file),
                "module_info": {"name": module_name, "id": module_id, "os": module_os, "arch": module_arch},
            }

        except ToolExecutionError as e:
            return {"success": False, "error": f"dump_syms execution failed: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to extract symbols: {str(e)}"}
