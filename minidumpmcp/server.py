"""FastMCP server entry point."""

import asyncio

from fastmcp import FastMCP
from minidumpmcp.prompts import CrashAnalysisProvider
from minidumpmcp.tools.stackwalk import StackwalkProvider


async def run_mcp_server() -> None:
    # Initialize FastMCP and register tools and prompts
    mcp: FastMCP[None] = FastMCP(name="minidump-mcp")

    # Register tools
    stackwalk_provider = StackwalkProvider()
    mcp.tool(stackwalk_provider.stackwalk_minidump)

    # Register crash analysis prompts
    crash_provider = CrashAnalysisProvider()
    mcp.prompt(crash_provider.crash_analyzer)
    mcp.prompt(crash_provider.stack_interpreter)
    mcp.prompt(crash_provider.exception_decoder)
    mcp.prompt(crash_provider.symbol_advisor)

    try:
        await mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=8000,
            log_level="debug",
        )
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("Server shutdown initiated...")
        # FastMCP might not have explicit shutdown method,
        # but cancellation should stop the server
        raise


def main() -> None:
    """Entry point for the minidump-mcp command."""
    try:
        asyncio.run(run_mcp_server())
    except KeyboardInterrupt:
        print("\nGracefully shutting down...")
    except asyncio.CancelledError:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
