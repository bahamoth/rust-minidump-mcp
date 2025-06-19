"""Stackwalk tools for FastMCP."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from ._common import ToolExecutionError, run_subprocess, which


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
            return {"error": f"Minidump file not found: {minidump_path}", "success": False}

        if not minidump_file.is_file():
            return {"error": f"Path is not a file: {minidump_path}", "success": False}

        # Get absolute path to the minidump-stackwalk binary
        project_root = Path(__file__).parent.parent.parent
        stackwalk_binary = project_root / "tools" / "bin" / "minidump-stackwalk"

        # If not found in project tools, try to find it on PATH
        if not stackwalk_binary.exists():
            which_result = which("minidump-stackwalk")
            if which_result:
                stackwalk_binary = Path(which_result)
            else:
                return {
                    "error": (
                        f"minidump-stackwalk binary not found at: {stackwalk_binary}. "
                        "Run 'uv run just install-tools' first or ensure minidump-stackwalk is on PATH."
                    ),
                    "success": False,
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
                return {"error": f"Symbols directory not found or not a directory: {symbols_path}", "success": False}

        try:
            # Execute minidump-stackwalk with timeout using async helper
            stdout = await run_subprocess(cmd, timeout=30.0)

            if output_format == "json":
                try:
                    # Parse JSON output
                    parsed_output = json.loads(stdout)
                    return {"success": True, "data": parsed_output, "command": " ".join(str(c) for c in cmd)}
                except json.JSONDecodeError as e:
                    return {"error": f"Failed to parse JSON output: {e}", "raw_output": stdout, "success": False}
            else:
                # Return raw text output
                return {"success": True, "data": stdout, "command": " ".join(str(c) for c in cmd)}

        except ToolExecutionError as e:
            return {
                "error": f"minidump-stackwalk execution failed: {e}",
                "command": " ".join(str(c) for c in cmd),
                "success": False,
            }

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}
