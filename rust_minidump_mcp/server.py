"""FastMCP server entry point."""

from fastmcp import FastMCP

mcp: FastMCP[None] = FastMCP(name="RustMinidumpMcp")


async def main() -> None:
    await mcp.run_async(transport="streamable-http", host="0.0.0.0", port=8080)
