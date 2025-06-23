import asyncio
from typing import Any

import typer
from fastmcp import Client
from mcp import Tool
from rich import print_json

default_config = {
    "RustMinidumpMcp": {
        "url": "http://localhost:8000/mcp",
        "transport": "streamable-http",
    }
}

app = typer.Typer()
mcp_client: Client[Any] = Client(default_config)


@app.command("client")
def client() -> None:
    """Run the MCP client."""
    typer.echo("Starting MCP client...")
    asyncio.run(list_tools())


async def list_tools() -> None:
    async with mcp_client:
        tools: list[Tool] = await mcp_client.list_tools()

        typer.echo("Available tools:")
        for tool in tools:
            typer.echo(f"- {tool.name}: {tool.description}")

        output = await mcp_client.call_tool(
            "stackwalk_minidump",
            {
                "minidump_path": "tests/testdata/test.dmp",
                "symbols_path": "tests/testdata/symbols/test_app.pdb",
            },
        )
        typer.echo("Callstacks:")
        for callstack in output:
            if callstack.type == "text":
                print_json(callstack.text)

        prompts = await mcp_client.list_prompts()
        typer.echo("Available prompts:")
        for prompt in prompts:
            typer.echo(f"- {prompt.name}: {prompt.description}")
            for arg in prompt.arguments if prompt.arguments else []:
                typer.echo(f"  - {arg.name}: {arg.description} (required: {arg.required})")


@app.command("server")
def server(
    name: str = typer.Option("minidump-mcp", help="Server name"),
    transport: str = typer.Option("streamable-http", help="Transport type (stdio, streamable-http, sse)"),
    log_level: str = typer.Option("INFO", help="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    host: str = typer.Option("127.0.0.1", help="Host for HTTP/SSE transports"),
    port: int = typer.Option(8000, help="Port for HTTP/SSE transports"),
    path: str = typer.Option("/mcp", help="Path for HTTP/SSE transports"),
    message_path: str = typer.Option("/message", help="Message path for SSE transport"),
) -> None:
    """Run the MCP server with specified configuration.

    Examples:
        minidump-mcp server                                    # STDIO transport
        minidump-mcp server --transport streamable-http        # HTTP transport
        minidump-mcp server --transport sse --port 9000        # SSE transport on port 9000

    Environment variables can also be used:
        MINIDUMP_MCP_TRANSPORT=streamable-http
        MINIDUMP_MCP_STREAMABLE_HTTP__HOST=0.0.0.0
        MINIDUMP_MCP_STREAMABLE_HTTP__PORT=8080
    """
    import os

    from minidumpmcp.config import ServerSettings

    # Create settings with CLI arguments overriding defaults and env vars
    settings_kwargs: dict[str, Any] = {}

    # Only set non-default values to allow env vars to take precedence
    if name != "minidump-mcp":
        settings_kwargs["name"] = name
    if transport != "stdio":
        settings_kwargs["transport"] = transport
    if log_level != "INFO":
        settings_kwargs["log_level"] = log_level

    # For HTTP/SSE specific settings, we need to handle nested config
    if transport in ["streamable-http", "sse"]:
        # Set environment variables for nested config if CLI args are provided
        if host != "127.0.0.1":
            if transport == "streamable-http":
                os.environ["MINIDUMP_MCP_STREAMABLE_HTTP__HOST"] = host
            else:  # sse
                os.environ["MINIDUMP_MCP_SSE__HOST"] = host

        if port != 8000:
            if transport == "streamable-http":
                os.environ["MINIDUMP_MCP_STREAMABLE_HTTP__PORT"] = str(port)
            else:  # sse
                os.environ["MINIDUMP_MCP_SSE__PORT"] = str(port)

        if path != "/mcp":
            if transport == "streamable-http":
                os.environ["MINIDUMP_MCP_STREAMABLE_HTTP__PATH"] = path
            else:  # sse
                os.environ["MINIDUMP_MCP_SSE__PATH"] = path

        if transport == "sse" and message_path != "/message":
            os.environ["MINIDUMP_MCP_SSE__MESSAGE_PATH"] = message_path

    # Create settings and run server
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
