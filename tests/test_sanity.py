import importlib
import sys
from pathlib import Path

# Ensure package import works when tests run in isolation
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_import_server() -> None:
    """Ensure the FastMCP server can be imported."""
    importlib.import_module("rust_minidump_mcp.server")
