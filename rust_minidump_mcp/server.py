"""FastMCP server entry point."""
import asyncio

from fastmcp import FastMCP

mcp: FastMCP[None] = FastMCP(name="RustMinidumpMcp")


async def main() -> None:
    await mcp.run_async(transport="streamable-http", host="0.0.0.0", port=8080)

if __name__ == "__main__":
    asyncio.run(main())
