

import asyncio
import json
from typing import Any

from rich import print_json
import typer
from fastmcp import Client
from mcp import Tool

default_config = {
        "RustMinidumpMcp": {
            "url": "http://localhost:8000/mcp",
            "transport": "streamable-http",
        }
    }

app = typer.Typer()
mcp_client: Client[Any] = Client(default_config)

@app.command()
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
                }
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


if __name__ == "__main__":
    app()
