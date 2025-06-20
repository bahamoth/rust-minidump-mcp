"""FastMCP server entry point."""

import asyncio

from fastmcp import FastMCP

from minidumpmcp.prompts import CrashAnalysisProvider
from minidumpmcp.tools.stackwalk import StackwalkProvider


async def main() -> None:
    # Initialize FastMCP and register tools and prompts
    mcp: FastMCP[None] = FastMCP(name="RustMinidumpMcp")

    # Register tools
    stackwalk_provider = StackwalkProvider()
    mcp.tool(stackwalk_provider.stackwalk_minidump)

    # Register crash analysis prompts
    crash_provider = CrashAnalysisProvider()
    mcp.prompt(crash_provider.crash_analyzer)
    mcp.prompt(crash_provider.stack_interpreter)
    mcp.prompt(crash_provider.exception_decoder)
    mcp.prompt(crash_provider.symbol_advisor)

    await mcp.run_async(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
    )


if __name__ == "__main__":
    asyncio.run(main())
