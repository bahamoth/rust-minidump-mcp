"""Stackwalk tools for FastMCP."""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


class StackwalkProvider:
    """Provider for minidump stackwalk tools."""

    def stackwalk_minidump(
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
            subprocess.CalledProcessError: If minidump-stackwalk execution fails
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

        if not stackwalk_binary.exists():
            return {
                "error": (
                    f"minidump-stackwalk binary not found at: {stackwalk_binary}. "
                    "Run 'uv run just install-tools' first."
                ),
                "success": False,
            }

        # Build command
        cmd = [str(stackwalk_binary)]

        if output_format == "json":
            cmd.append("--json")

        cmd.append(str(minidump_file.absolute()))

        # Add symbols path if provided
        if symbols_path:
            symbols_dir = Path(symbols_path)
            if symbols_dir.exists() and symbols_dir.is_dir():
                cmd.extend(["--symbols-path", str(symbols_dir.absolute())])
            else:
                return {"error": f"Symbols directory not found or not a directory: {symbols_path}", "success": False}

        try:
            # Execute minidump-stackwalk with timeout
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)  # 30 second timeout

            if output_format == "json":
                try:
                    # Parse JSON output
                    parsed_output = json.loads(result.stdout)
                    return {"success": True, "data": parsed_output, "command": " ".join(cmd)}
                except json.JSONDecodeError as e:
                    return {"error": f"Failed to parse JSON output: {e}", "raw_output": result.stdout, "success": False}
            else:
                # Return raw text output
                return {"success": True, "data": result.stdout, "command": " ".join(cmd)}

        except subprocess.TimeoutExpired:
            return {"error": "minidump-stackwalk execution timed out (30s limit)", "success": False}

        except subprocess.CalledProcessError as e:
            return {
                "error": f"minidump-stackwalk failed with exit code {e.returncode}",
                "stderr": e.stderr,
                "stdout": e.stdout,
                "command": " ".join(cmd),
                "success": False,
            }

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}
