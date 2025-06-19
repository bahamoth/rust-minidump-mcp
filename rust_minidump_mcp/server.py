"""FastMCP server entry point."""

# import asyncio

from fastmcp import FastMCP

from tools.stackwalk import StackwalkProvider

# Initialize FastMCP and register tools
mcp: FastMCP[None] = FastMCP(name="RustMinidumpMcp")

# Register tools during initialization
stackwalk_provider = StackwalkProvider()
mcp.tool(stackwalk_provider.stackwalk_minidump)

def main() -> None:
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
    )


if __name__ == "__main__":
    main()
