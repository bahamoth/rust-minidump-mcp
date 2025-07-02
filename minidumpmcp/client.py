"""MCP client commands for interacting with the minidump server."""

import asyncio
import json
from typing import Any, Dict, List, Optional

import typer
from fastmcp import Client
from mcp import Tool
from mcp.types import Prompt, TextContent
from rich import print_json
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from minidumpmcp.client_validators.validators import ArgumentValidator, ParameterConverter
from minidumpmcp.config.client_settings import ClientSettings
from minidumpmcp.exceptions import ConfigurationError

# Create client app for subcommands
client_app = typer.Typer(help="MCP client commands")
console = Console()


def _create_client_settings(
    url: Optional[str] = None,
    transport: Optional[str] = None,
    timeout: Optional[float] = None,
) -> ClientSettings:
    """Create client settings from CLI arguments."""
    settings_kwargs: Dict[str, Any] = {}
    if url is not None:
        settings_kwargs["url"] = url
    if transport is not None:
        settings_kwargs["transport"] = transport
    if timeout is not None:
        settings_kwargs["timeout"] = timeout

    try:
        return ClientSettings(**settings_kwargs)
    except ValueError as e:
        error_str = str(e)
        if "transport" in error_str:
            error = ConfigurationError("transport", transport or "invalid", error_str)
        elif "timeout" in error_str:
            error = ConfigurationError("timeout", timeout or "invalid", error_str)
        else:
            error = ConfigurationError("client", "settings", error_str)

        typer.echo(f"\nError: {error.message}", err=True)
        if error.suggestion:
            typer.echo(f"Suggestion: {error.suggestion}", err=True)
        raise typer.Exit(1) from e


@client_app.command("list-tools")
def list_tools(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Server URL"),
    transport: Optional[str] = typer.Option(
        None, "--transport", "-t", help="Transport type: stdio, streamable-http, sse"
    ),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="Request timeout in seconds"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
) -> None:
    """List available tools from the server."""
    settings = _create_client_settings(url, transport, timeout)
    asyncio.run(_list_tools(settings, detailed))


async def _list_tools(settings: ClientSettings, detailed: bool) -> None:
    """List tools implementation."""
    async with Client(settings.config_dict) as client:
        tools = await client.list_tools()

        if detailed:
            for tool in tools:
                console.print(f"\n[bold cyan]{tool.name}[/bold cyan]")
                console.print(f"Description: {tool.description or 'No description'}")
                if tool.inputSchema:
                    console.print("Parameters:")
                    _print_schema(tool.inputSchema)
        else:
            table = _format_tools_table(tools)
            console.print(table)


@client_app.command("list-prompts")
def list_prompts(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Server URL"),
    transport: Optional[str] = typer.Option(
        None, "--transport", "-t", help="Transport type: stdio, streamable-http, sse"
    ),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="Request timeout in seconds"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
) -> None:
    """List available prompts from the server."""
    settings = _create_client_settings(url, transport, timeout)
    asyncio.run(_list_prompts(settings, detailed))


async def _list_prompts(settings: ClientSettings, detailed: bool) -> None:
    """List prompts implementation."""
    async with Client(settings.config_dict) as client:
        prompts = await client.list_prompts()

        if detailed:
            for prompt in prompts:
                console.print(f"\n[bold cyan]{prompt.name}[/bold cyan]")
                console.print(f"Description: {prompt.description or 'No description'}")
                if prompt.arguments:
                    console.print("Arguments:")
                    for arg in prompt.arguments:
                        required = "[red]required[/red]" if arg.required else "[green]optional[/green]"
                        console.print(f"  - {arg.name} ({required}): {arg.description}")
        else:
            table = _format_prompts_table(prompts)
            console.print(table)


@client_app.command("describe-tool")
def describe_tool(
    name: str = typer.Argument(..., help="Tool name to describe"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Server URL"),
    transport: Optional[str] = typer.Option(
        None, "--transport", "-t", help="Transport type: stdio, streamable-http, sse"
    ),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="Request timeout in seconds"),
) -> None:
    """Get detailed information about a specific tool."""
    settings = _create_client_settings(url, transport, timeout)
    asyncio.run(_describe_tool(settings, name))


async def _describe_tool(settings: ClientSettings, name: str) -> None:
    """Describe tool implementation."""
    async with Client(settings.config_dict) as client:
        tools = await client.list_tools()
        tool = next((t for t in tools if t.name == name), None)

        if tool:
            console.print(f"\n[bold cyan]{tool.name}[/bold cyan]")
            console.print(f"Description: {tool.description or 'No description'}")
            if tool.inputSchema:
                console.print("\nParameters:")
                _print_schema(tool.inputSchema)
        else:
            console.print(f"[red]Tool '{name}' not found[/red]")


@client_app.command("describe-prompt")
def describe_prompt(
    name: str = typer.Argument(..., help="Prompt name to describe"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Server URL"),
    transport: Optional[str] = typer.Option(
        None, "--transport", "-t", help="Transport type: stdio, streamable-http, sse"
    ),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="Request timeout in seconds"),
) -> None:
    """Get detailed information about a specific prompt."""
    settings = _create_client_settings(url, transport, timeout)
    asyncio.run(_describe_prompt(settings, name))


async def _describe_prompt(settings: ClientSettings, name: str) -> None:
    """Describe prompt implementation."""
    async with Client(settings.config_dict) as client:
        prompts = await client.list_prompts()
        prompt = next((p for p in prompts if p.name == name), None)

        if prompt:
            console.print(f"\n[bold cyan]{prompt.name}[/bold cyan]")
            console.print(f"Description: {prompt.description or 'No description'}")
            if prompt.arguments:
                console.print("\nArguments:")
                for arg in prompt.arguments:
                    required = "[red]required[/red]" if arg.required else "[green]optional[/green]"
                    console.print(f"  - {arg.name} ({required}): {arg.description}")
        else:
            console.print(f"[red]Prompt '{name}' not found[/red]")


@client_app.command("call-tool")
def call_tool(
    name: str = typer.Argument(..., help="Tool name to call"),
    args: Optional[str] = typer.Option(None, "--args", help="Arguments as JSON object string"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Server URL"),
    transport: Optional[str] = typer.Option(
        None, "--transport", "-t", help="Transport type: stdio, streamable-http, sse"
    ),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="Request timeout in seconds"),
) -> None:
    """Call a tool with specified parameters.

    Examples:
        rust-minidump-mcp client call-tool stackwalk_minidump \\
            --args '{"minidump_path": "/path/to/dump.dmp", "symbols_path": "/path/to/symbols"}'
    """
    settings = _create_client_settings(url, transport, timeout)

    if args:
        try:
            parsed = ParameterConverter.parse_json_arguments(args)
            # Convert all values to strings for MCP protocol compliance
            arguments = ParameterConverter.convert_to_mcp_format(parsed)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1) from e
    else:
        arguments = {}

    asyncio.run(_call_tool(settings, name, arguments))


async def _call_tool(settings: ClientSettings, name: str, arguments: Dict[str, Any]) -> None:
    """Call tool implementation."""
    async with Client(settings.config_dict) as client:
        try:
            console.print(f"[yellow]Calling tool '{name}'...[/yellow]")
            result = await client.call_tool(name, arguments)

            # Extract text content if result contains TextContent objects
            if isinstance(result, list):
                text_parts = []
                for item in result:
                    if hasattr(item, "text"):
                        text_parts.append(item.text)
                    else:
                        text_parts.append(str(item))
                result = "\n".join(text_parts)

            console.print("\n[green]Result:[/green]")
            print_json(data=result)
        except Exception as e:
            console.print(f"[red]Error calling tool: {e}[/red]")
            raise typer.Exit(1) from e


@client_app.command("call-prompt")
def call_prompt(
    name: str = typer.Argument(..., help="Prompt name to call"),
    args: Optional[str] = typer.Option(None, "--args", help="Arguments as JSON object string"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Server URL"),
    transport: Optional[str] = typer.Option(
        None, "--transport", "-t", help="Transport type: stdio, streamable-http, sse"
    ),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="Request timeout in seconds"),
) -> None:
    """Call a prompt with specified parameters.

    Examples:
        rust-minidump-mcp client call-prompt analyze_technical_details \\
            --args '{"stackwalk_output": "{\"crash\": \"data\"}", "technical_focus": "all"}'

        rust-minidump-mcp client call-prompt analyze_crash_end_to_end \\
            --args '{"dump_path": "/path/to/dump.dmp", "symbol_sources": "[\"/path/to/symbols\"]"}'
    """
    settings = _create_client_settings(url, transport, timeout)

    if args:
        try:
            parsed = ParameterConverter.parse_json_arguments(args)
            # Convert all values to strings for MCP protocol compliance
            arguments = ParameterConverter.convert_to_mcp_format(parsed)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1) from e
    else:
        arguments = {}

    asyncio.run(_call_prompt(settings, name, arguments))


async def _call_prompt(settings: ClientSettings, name: str, arguments: Dict[str, Any]) -> None:
    """Call prompt implementation."""
    async with Client(settings.config_dict) as client:
        try:
            # First, get prompt metadata to validate arguments
            prompts = await client.list_prompts()
            prompt = next((p for p in prompts if p.name == name), None)

            if not prompt:
                console.print(f"[red]Error: Prompt '{name}' not found[/red]")
                raise typer.Exit(1)

            # Validate all arguments at once
            validation_errors = ArgumentValidator.validate_prompt_arguments(prompt, arguments)
            if validation_errors:
                console.print("[red]Error: Invalid arguments:[/red]")
                for error in validation_errors:
                    console.print(f"  - {error}")
                _print_prompt_usage(name, prompt)
                raise typer.Exit(1)

            console.print(f"[yellow]Calling prompt '{name}'...[/yellow]")
            result = await client.get_prompt(name, arguments)

            # Extract text content from messages
            text_parts = []
            for message in result.messages:
                if message.content and isinstance(message.content, TextContent):
                    text_parts.append(message.content.text)

            console.print("\n[green]Result:[/green]")
            console.print("\n\n".join(text_parts))
        except Exception as e:
            import traceback

            console.print(f"[red]Error calling prompt: {e}[/red]")
            console.print("[yellow]Full traceback:[/yellow]")
            traceback.print_exc()
            raise typer.Exit(1) from e


def _format_tools_table(tools: List[Tool]) -> Table:
    """Format tools as a rich table."""
    table = Table(title="Available Tools")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")

    for tool in tools:
        # Extract first line of description for simple view
        desc = tool.description or ""
        first_line = desc.split("\n")[0].strip()
        if first_line.endswith("."):
            first_line = first_line[:-1]  # Remove trailing period
        table.add_row(tool.name, first_line)

    return table


def _format_prompts_table(prompts: List[Prompt]) -> Table:
    """Format prompts as a rich table."""
    table = Table(title="Available Prompts")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")

    for prompt in prompts:
        # Extract first non-empty line of description
        desc = prompt.description or ""
        lines = desc.split("\n")
        first_line = ""
        for line in lines:
            line = line.strip()
            if line:
                first_line = line
                break

        table.add_row(prompt.name, first_line)

    return table


def _print_schema(schema: Dict[str, Any], indent: int = 2) -> None:
    """Print JSON schema in a readable format."""
    if "properties" in schema:
        required = schema.get("required", [])
        for prop_name, prop_schema in schema["properties"].items():
            prop_type = prop_schema.get("type", "any")
            description = prop_schema.get("description", "")
            is_required = prop_name in required

            indent_str = " " * indent
            req_str = "[red]required[/red]" if is_required else "[green]optional[/green]"
            console.print(f"{indent_str}- {prop_name} ({prop_type}) {req_str}")
            if description:
                console.print(f"{indent_str}  {description}")


def _print_prompt_usage(name: str, prompt: Prompt) -> None:
    """Print detailed usage information for a prompt."""
    console.print(f"\n[yellow]Valid arguments for '{name}':[/yellow]")

    # Build example JSON
    example_json = {}

    if not prompt.arguments:
        return

    for arg in prompt.arguments:
        req = "[red]required[/red]" if arg.required else "[green]optional[/green]"
        console.print(f"\n  [bold]{arg.name}[/bold] ({req})")

        if arg.description:
            schema = ArgumentValidator.parse_schema_from_description(arg.description)
            if schema:
                # Extract type and enum info
                enum_values = ArgumentValidator.extract_enum_values(schema)
                if enum_values:
                    console.print("    Type: string (enum)")
                    console.print(f"    Values: {enum_values}")
                    # Use first enum value as example
                    example_json[arg.name] = enum_values[0]
                else:
                    # Generic type info from schema
                    if "type" in schema:
                        console.print(f"    Type: {schema['type']}")
                    elif "anyOf" in schema:
                        types = [opt.get("type", "any") for opt in schema["anyOf"] if "type" in opt]
                        console.print(f"    Type: {' or '.join(types)}")

                    # Build example value
                    if "object" in str(schema):
                        example_json[arg.name] = '{"key": "value"}'
                    elif "array" in str(schema):
                        example_json[arg.name] = '["item1", "item2"]'
                    else:
                        example_json[arg.name] = "example_value"
            else:
                console.print(f"    {arg.description}")
                example_json[arg.name] = "value"

    # Pretty print example
    console.print("\n[yellow]Example usage:[/yellow]")
    pretty_json = json.dumps(example_json, indent=2)
    syntax = Syntax(pretty_json, "json", theme="monokai", line_numbers=False)
    console.print("    --args '", end="")
    console.print(syntax, end="")
    console.print("'")
