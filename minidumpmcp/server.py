"""FastMCP server entry point."""

# import asyncio

import asyncio

from fastmcp import FastMCP

from minidumpmcp.tools.stackwalk import StackwalkProvider


async def main() -> None:
    # Initialize FastMCP and register tools
    mcp: FastMCP[None] = FastMCP(name="RustMinidumpMcp")

    # Register tools during initialization
    stackwalk_provider = StackwalkProvider()
    mcp.tool(stackwalk_provider.stackwalk_minidump)

    await mcp.run_async(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
    )


if __name__ == "__main__":
    asyncio.run(main())
