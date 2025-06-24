"""Stackwalk tools for FastMCP."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from minidumpmcp.exceptions import (
    FileValidationError,
    MinidumpAnalysisError,
    ToolNotFoundError,
)
from minidumpmcp.exceptions import (
    ToolExecutionError as CommonToolExecutionError,
)

from ._common import ToolExecutionError, run_subprocess, which


def _get_bin_path(bin_name: str) -> Path:
    """Get the path to the bin directory."""
    prefix = Path(__file__).parent / "bin"
    match sys.platform:
        case "linux":
            return Path(prefix / f"{bin_name}-linux")
        case "darwin":
            return Path(prefix / f"{bin_name}-macos")
        case "win32":
            return Path(prefix / f"{bin_name}-windows")
        case _:
            raise ValueError("Unsupported platform")


class StackwalkProvider:
    """Provider for minidump stackwalk tools."""

    async def stackwalk_minidump(
        self, minidump_path: str, symbols_path: Optional[str] = None, output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Analyze a minidump file using minidump-stackwalk CLI tool.

        Args:
            minidump_path: Path to the minidump file (.dmp)
            symbols_path: Optional path to symbols directory
            output_format: Output format (json, text) - defaults to json

        Returns:
            Dictionary containing crash analysis results

        Raises:
            FileNotFoundError: If minidump file or CLI tool not found
            ToolExecutionError: If minidump-stackwalk execution fails
            json.JSONDecodeError: If output parsing fails
        """
        # Validate input file
        minidump_file = Path(minidump_path)
        if not minidump_file.exists():
            file_error = FileValidationError(minidump_file, "File not found")
            return {"error": str(file_error), "success": False, "error_code": file_error.error_code}

        if not minidump_file.is_file():
            file_error = FileValidationError(minidump_file, "Path is not a file")
            return {"error": str(file_error), "success": False, "error_code": file_error.error_code}

        # Get absolute path to the minidump-stackwalk binary
        # project_root = Path(__file__).parent.parent.parent

        stackwalk_binary = _get_bin_path("minidump-stackwalk")

        # If not found in project tools, try to find it on PATH
        if not stackwalk_binary.exists():
            which_result = which("minidump-stackwalk")
            if which_result:
                stackwalk_binary = Path(which_result)
            else:
                tool_error = ToolNotFoundError("minidump-stackwalk", [stackwalk_binary])
                return {
                    "error": str(tool_error),
                    "success": False,
                    "error_code": tool_error.error_code,
                }

        # Build command
        cmd: list[str | Path] = [stackwalk_binary]

        if output_format == "json":
            cmd.append("--json")

        cmd.append(minidump_file.absolute())

        # Add symbols path if provided
        if symbols_path:
            symbols_dir = Path(symbols_path)
            if symbols_dir.exists() and symbols_dir.is_dir():
                cmd.extend(["--symbols-path", symbols_dir.absolute()])
            else:
                symbols_error = FileValidationError(symbols_dir, "Symbols directory not found or not a directory")
                return {"error": str(symbols_error), "success": False, "error_code": symbols_error.error_code}

        try:
            # Execute minidump-stackwalk with timeout using async helper
            stdout = await run_subprocess(cmd, timeout=30.0)

            if output_format == "json":
                try:
                    # Parse JSON output
                    parsed_output = json.loads(stdout)
                    return {"success": True, "data": parsed_output, "command": " ".join(str(c) for c in cmd)}
                except json.JSONDecodeError as e:
                    parse_error = MinidumpAnalysisError(
                        minidump_file,
                        "Failed to parse analysis output",
                        {"parse_error": str(e), "raw_output": stdout[:500]},  # Limit output size
                    )
                    return {"error": str(parse_error), "success": False, "error_code": parse_error.error_code}
            else:
                # Return raw text output
                return {"success": True, "data": stdout, "command": " ".join(str(c) for c in cmd)}

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
                "minidump-stackwalk",
                [str(c) for c in cmd],
                exit_code,
                stderr,
            )
            return {
                "error": str(exec_error),
                "command": " ".join(str(c) for c in cmd),
                "success": False,
                "error_code": exec_error.error_code,
            }

        except Exception as e:
            unexpected_error = MinidumpAnalysisError(
                minidump_file,
                "Unexpected error during analysis",
                {"exception_type": type(e).__name__, "exception_message": str(e)},
            )
            return {"error": str(unexpected_error), "success": False, "error_code": unexpected_error.error_code}
