"""FastMCP server entry point."""

import asyncio
import logging
from typing import cast

from fastmcp import FastMCP

from minidumpmcp.config import ServerSettings
from minidumpmcp.config.settings import SseTransportConfig, StreamableHttpConfig
from minidumpmcp.prompts import CrashAnalysisProvider
from minidumpmcp.prompts.symbol_preparation_provider import SymbolPreparationProvider
from minidumpmcp.tools.dump_syms import DumpSymsTool
from minidumpmcp.tools.stackwalk import StackwalkProvider


def setup_logging(settings: ServerSettings) -> None:
    """Configure logging based on settings."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def run_mcp_server(settings: ServerSettings | None = None) -> None:
    """Run the MCP server with configuration from settings."""
    # Load configuration
    if settings is None:
        settings = ServerSettings()

    # Setup logging
    setup_logging(settings)
    logger = logging.getLogger(__name__)

    logger.info("Starting %s with %s transport", settings.name, settings.transport)

    # Initialize FastMCP and register tools and prompts
    mcp: FastMCP[None] = FastMCP(name=settings.name)

    # Register tools
    stackwalk_provider = StackwalkProvider()
    mcp.tool(stackwalk_provider.stackwalk_minidump)

    dump_syms_tool = DumpSymsTool()
    mcp.tool(dump_syms_tool.extract_symbols)

    # Register crash analysis prompts
    crash_provider = CrashAnalysisProvider()
    mcp.prompt(crash_provider.analyze_crash_with_expertise)
    mcp.prompt(crash_provider.analyze_technical_details)

    # Register symbol preparation prompts
    symbol_provider = SymbolPreparationProvider()
    mcp.prompt(symbol_provider.symbol_transformation_guide)

    # Build run_async arguments based on transport configuration
    try:
        match settings.transport:
            case "stdio":
                logger.info("Starting STDIO transport")
                await mcp.run_async(transport="stdio")
            case "streamable-http":
                http_config = cast(StreamableHttpConfig, settings.transport_config)
                logger.info("Starting Streamable HTTP transport on %s:%s", http_config.host, http_config.port)
                await mcp.run_async(
                    transport="streamable-http",
                    host=http_config.host,
                    port=http_config.port,
                    path=http_config.path,
                )
            case "sse":
                sse_config = cast(SseTransportConfig, settings.transport_config)
                logger.info("Starting SSE transport on %s:%s", sse_config.host, sse_config.port)
                await mcp.run_async(
                    transport="sse",
                    host=sse_config.host,
                    port=sse_config.port,
                    path=sse_config.path,
                )
            case _:
                raise ValueError(f"Unsupported transport: {settings.transport}")

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Server shutdown initiated...")
        # FastMCP might not have explicit shutdown method,
        # but cancellation should stop the server
        raise


def main() -> None:
    """Entry point for the rust-minidump-mcp command."""
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
