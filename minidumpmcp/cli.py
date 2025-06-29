"""CLI interface for minidump-mcp server and client."""

import asyncio
from typing import Any, Dict

import typer

from minidumpmcp.client import client_app

app = typer.Typer()

# Add client subcommands
app.add_typer(client_app, name="client")


@app.command("server")
def server(
    name: str = typer.Option("minidump-mcp", help="Server name"),
    transport: str = typer.Option("stdio", help="Transport type (stdio, streamable-http, sse)"),
    log_level: str = typer.Option("INFO", help="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    host: str = typer.Option("127.0.0.1", help="Host for HTTP/SSE transports"),
    port: int = typer.Option(8000, help="Port for HTTP/SSE transports"),
    path: str = typer.Option("/mcp", help="Path for HTTP/SSE transports"),
    message_path: str = typer.Option("/message", help="Message path for SSE transport"),
) -> None:
    """Run the MCP server with specified configuration.

    Examples:
        rust-minidump-mcp server                                    # STDIO transport (default)
        rust-minidump-mcp server --transport streamable-http        # HTTP transport
        rust-minidump-mcp server --transport sse --port 9000        # SSE transport on port 9000

    Environment variables can also be used:
        MINIDUMP_MCP_TRANSPORT=streamable-http
        MINIDUMP_MCP_STREAMABLE_HTTP__HOST=0.0.0.0
        MINIDUMP_MCP_STREAMABLE_HTTP__PORT=8080
    """
    from minidumpmcp.config import ServerSettings
    from minidumpmcp.config.settings import SseTransportConfig, StreamableHttpConfig

    # Create settings with CLI arguments
    # settings_customise_sources will handle priority: CLI > env > .env > defaults
    settings_kwargs: Dict[str, Any] = {
        "name": name,
        "transport": transport,
        "log_level": log_level,
    }

    # Handle transport-specific configurations
    if transport == "streamable-http":
        settings_kwargs["streamable_http"] = StreamableHttpConfig(
            host=host,
            port=port,
            path=path,
        )
    elif transport == "sse":
        settings_kwargs["sse"] = SseTransportConfig(
            host=host,
            port=port,
            path=path,
            message_path=message_path,
        )

    # Create settings
    settings = ServerSettings(**settings_kwargs)

    typer.echo(f"Starting {settings.name} with {settings.transport} transport")
    if settings.transport != "stdio":
        from minidumpmcp.config.settings import HttpTransportConfig

        config = settings.transport_config
        if isinstance(config, HttpTransportConfig):
            typer.echo(f"Server will be available on {config.host}:{config.port}")

    # Import and run the server
    from minidumpmcp.server import run_mcp_server

    asyncio.run(run_mcp_server(settings))


@app.callback()
def main() -> None:
    """MiniDump MCP CLI Tool."""
    pass


if __name__ == "__main__":
    app()
