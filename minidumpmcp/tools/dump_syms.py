"""dump_syms tool provider for extracting symbols from binaries."""

import platform
from pathlib import Path
from typing import Any, Dict, Optional

from minidumpmcp.exceptions import (
    FileValidationError,
    SymbolExtractionError,
    ToolNotFoundError,
)
from minidumpmcp.exceptions import (
    ToolExecutionError as CommonToolExecutionError,
)

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
                file_error = FileValidationError(binary_file, "Binary file not found")
                return {"success": False, "error": str(file_error), "error_code": file_error.error_code}

            # Set output directory
            if output_dir:
                output_path = Path(output_dir).resolve()
            else:
                output_path = Path.cwd() / "symbols"

            output_path.mkdir(parents=True, exist_ok=True)

            # Get dump_syms binary
            try:
                dump_syms = _get_dump_syms_path()
            except ValueError as e:
                platform_error = SymbolExtractionError(binary_file, str(e))
                return {"success": False, "error": str(platform_error), "error_code": platform_error.error_code}

            if not dump_syms.exists():
                tool_error = ToolNotFoundError("dump_syms", [dump_syms])
                return {
                    "success": False,
                    "error": str(tool_error),
                    "error_code": tool_error.error_code,
                }

            # Run dump_syms to extract symbols
            cmd = [str(dump_syms), str(binary_file)]
            stdout = await run_subprocess(cmd)

            # Parse the symbol data
            if not stdout:
                output_error = SymbolExtractionError(binary_file, "dump_syms produced no output")
                return {"success": False, "error": str(output_error), "error_code": output_error.error_code}

            # Extract module info from first line
            # Format: MODULE <os> <arch> <id> <name>
            first_line = stdout.split("\n")[0]
            parts = first_line.split()

            if len(parts) < 5 or parts[0] != "MODULE":
                header_error = SymbolExtractionError(
                    binary_file,
                    f"Invalid symbol header format. Expected 'MODULE <os> <arch> <id> <name>', got: {first_line}",
                )
                return {"success": False, "error": str(header_error), "error_code": header_error.error_code}

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
            # Convert common tool error to our custom error
            error_msg = str(e)
            exit_code = 1  # Default exit code
            stderr = ""

            # Try to extract exit code from error message
            if "exit-code" in error_msg:
                try:
                    exit_code = int(error_msg.split("exit-code")[1].split()[0])
                except (IndexError, ValueError):
                    pass

            # Extract stderr if present
            if "\n" in error_msg:
                stderr = error_msg.split("\n", 1)[1]

            exec_error = CommonToolExecutionError(
                "dump_syms",
                [str(c) for c in cmd],
                exit_code,
                stderr,
            )
            return {"success": False, "error": str(exec_error), "error_code": exec_error.error_code}
        except Exception as e:
            unexpected_error = SymbolExtractionError(
                binary_file,
                f"Unexpected error: {type(e).__name__} - {str(e)}",
            )
            return {"success": False, "error": str(unexpected_error), "error_code": unexpected_error.error_code}
