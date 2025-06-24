import asyncio
import os
from typing import Any, Optional

import typer
from mcp import Tool
from rich import print_json

from fastmcp import Client
from minidumpmcp.config.client_settings import ClientSettings
from minidumpmcp.exceptions import ConfigurationError
from minidumpmcp.exceptions import ConnectionError as MCPConnectionError

app = typer.Typer()


@app.command("client")
def client(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Server URL (overrides env/config)"),
    transport: Optional[str] = typer.Option(
        None,
        "--transport",
        "-t",
        help="Transport type: stdio, streamable-http, sse (overrides env/config)",
    ),
    timeout: Optional[float] = typer.Option(
        None,
        "--timeout",
        help="Request timeout in seconds (overrides env/config)",
    ),
) -> None:
    """Run the MCP client.

    Examples:
        minidump-mcp client                                           # Use defaults or env vars
        minidump-mcp client --url http://localhost:8080/mcp          # Custom URL
        minidump-mcp client --transport stdio                         # STDIO transport
        minidump-mcp client --timeout 60                              # 60 second timeout

    Environment variables can also be used:
        MINIDUMP_MCP_CLIENT_URL=http://localhost:8080/mcp
        MINIDUMP_MCP_CLIENT_TRANSPORT=streamable-http
        MINIDUMP_MCP_CLIENT_TIMEOUT=60
    """
    # Create settings with CLI arguments overriding defaults and env vars
    settings_kwargs: dict[str, Any] = {}

    if url is not None:
        settings_kwargs["url"] = url
    if transport is not None:
        settings_kwargs["transport"] = transport
    if timeout is not None:
        settings_kwargs["timeout"] = timeout

    # Create client settings
    try:
        settings = ClientSettings(**settings_kwargs)
    except ValueError as e:
        # Convert pydantic validation errors to our custom errors
        error_str = str(e)
        if "transport" in error_str:
            error = ConfigurationError("transport", transport or "invalid", error_str)
        elif "timeout" in error_str:
            error = ConfigurationError("timeout", timeout or "invalid", error_str)
        else:
            error = ConfigurationError("client", settings_kwargs, error_str)

        typer.echo(f"\nError: {error.message}", err=True)
        if error.suggestion:
            typer.echo(f"Suggestion: {error.suggestion}", err=True)
        raise typer.Exit(1) from e

    # Display connection info
    typer.echo("Connecting to server...")
    typer.echo(f"  Transport: {settings.transport}")
    if settings.transport != "stdio":
        typer.echo(f"  URL: {settings.url}")
    typer.echo(f"  Timeout: {settings.timeout}s")

    asyncio.run(run_client(settings))


async def run_client(settings: ClientSettings) -> None:
    """Run the client with given settings."""
    mcp_client: Client[Any] = Client(settings.config_dict)

    try:
        async with mcp_client:
            tools: list[Tool] = await mcp_client.list_tools()
    except Exception as e:
        # Create appropriate connection error
        error_str = str(e).lower()
        reason = str(e)

        if "connection refused" in error_str:
            reason = "Connection refused"
        elif "timeout" in error_str:
            reason = "Connection timeout"
        elif "404" in error_str or "not found" in error_str:
            reason = "Endpoint not found"

        error = MCPConnectionError(
            settings.url if settings.transport != "stdio" else "stdio://",
            reason,
            settings.transport,
        )

        typer.echo(f"\nError: {error.message}", err=True)
        if error.context:
            for key, value in error.context.items():
                typer.echo(f"  {key}: {value}", err=True)

        if error.suggestion:
            typer.echo(f"\nSuggestion: {error.suggestion}", err=True)

        raise typer.Exit(1) from e

    typer.echo("\nAvailable tools:")
    for tool in tools:
        typer.echo(f"- {tool.name}: {tool.description}")

    # Only run demo if test data exists
    test_dmp = "tests/testdata/test.dmp"
    if os.path.exists(test_dmp):
        typer.echo("\nRunning stackwalk demo...")
        try:
            output = await mcp_client.call_tool(
                "stackwalk_minidump",
                {
                    "minidump_path": test_dmp,
                    "symbols_path": "tests/testdata/symbols/test_app.pdb",
                },
            )
            typer.echo("\nCallstacks:")
            for callstack in output:
                if callstack.type == "text":
                    print_json(callstack.text)
        except Exception as e:
            typer.echo(f"Demo failed: {e}", err=True)

    prompts = await mcp_client.list_prompts()
    typer.echo("\nAvailable prompts:")
    for prompt in prompts:
        typer.echo(f"- {prompt.name}: {prompt.description}")
        for arg in prompt.arguments if prompt.arguments else []:
            typer.echo(f"  - {arg.name}: {arg.description} (required: {arg.required})")

    # Only run symbol extraction demo if test data exists
    test_elf = "tests/testdata/symbols.elf/basic.full"
    if os.path.exists(test_elf):
        typer.echo("\nRunning symbol extraction demo...")
        try:
            output = await mcp_client.call_tool(
                "extract_symbols",
                {
                    "binary_path": test_elf,
                    "output_dir": "output.txt",
                },
            )
            typer.echo(f"Extracted symbols: {output}")
        except Exception as e:
            typer.echo(f"Demo failed: {e}", err=True)


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
