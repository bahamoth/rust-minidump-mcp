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
from rich.prompt import Confirm, IntPrompt
from rich.prompt import Prompt as RichPrompt
from rich.table import Table

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
    params: List[str] = typer.Option([], "--param", "-p", help="Parameters in key=value format"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Server URL"),
    transport: Optional[str] = typer.Option(
        None, "--transport", "-t", help="Transport type: stdio, streamable-http, sse"
    ),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="Request timeout in seconds"),
) -> None:
    """Call a tool with specified parameters.

    Examples:
        rust-minidump-mcp client call-tool stackwalk_minidump \\
            --param minidump_path=/path/to/dump.dmp \\
            --param symbols_path=/path/to/symbols
    """
    settings = _create_client_settings(url, transport, timeout)
    try:
        arguments = _parse_params(params)
    except ValueError as e:
        console.print(f"[red]Error parsing parameters: {e}[/red]")
        raise typer.Exit(1) from e

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
    params: List[str] = typer.Option([], "--param", "-p", help="Parameters in key=value format"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Server URL"),
    transport: Optional[str] = typer.Option(
        None, "--transport", "-t", help="Transport type: stdio, streamable-http, sse"
    ),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="Request timeout in seconds"),
) -> None:
    """Call a prompt with specified parameters.

    Examples:
        rust-minidump-mcp client call-prompt analyze_crash_end_to_end \\
            --param dump_path=/path/to/dump.dmp \\
            --param 'symbol_sources=["/path/to/symbols"]'
    """
    settings = _create_client_settings(url, transport, timeout)
    try:
        arguments = _parse_params(params)
    except ValueError as e:
        console.print(f"[red]Error parsing parameters: {e}[/red]")
        raise typer.Exit(1) from e

    asyncio.run(_call_prompt(settings, name, arguments))


async def _call_prompt(settings: ClientSettings, name: str, arguments: Dict[str, Any]) -> None:
    """Call prompt implementation."""
    async with Client(settings.config_dict) as client:
        try:
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
            console.print(f"[red]Error calling prompt: {e}[/red]")
            raise typer.Exit(1) from e


@client_app.command("interactive")
def interactive(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Server URL"),
    transport: Optional[str] = typer.Option(
        None, "--transport", "-t", help="Transport type: stdio, streamable-http, sse"
    ),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="Request timeout in seconds"),
) -> None:
    """Run an interactive session with the MCP server."""
    settings = _create_client_settings(url, transport, timeout)
    asyncio.run(_interactive_session(settings))


async def _interactive_session(settings: ClientSettings) -> None:
    """Run an interactive session with the MCP server."""
    async with Client(settings.config_dict) as client:
        console.print("\n[bold cyan]MCP Interactive Client[/bold cyan]")
        console.print("Connected to server via", settings.transport)

        while True:
            console.print("\n[bold]Select an action:[/bold]")
            console.print("1. List tools")
            console.print("2. List prompts")
            console.print("3. Call a tool")
            console.print("4. Call a prompt")
            console.print("5. Exit")

            choice = IntPrompt.ask("Your choice", choices=["1", "2", "3", "4", "5"])

            if choice == 1:
                await _interactive_list_tools(client)
            elif choice == 2:
                await _interactive_list_prompts(client)
            elif choice == 3:
                await _interactive_call_tool(client)
            elif choice == 4:
                await _interactive_call_prompt(client)
            elif choice == 5:
                console.print("[yellow]Goodbye![/yellow]")
                break


async def _interactive_list_tools(client: Client[Any]) -> None:
    """Interactive tool listing."""
    tools = await client.list_tools()

    table = Table(title="Available Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")

    for tool in tools:
        table.add_row(tool.name, tool.description or "No description")

    console.print(table)

    if Confirm.ask("\nView tool details?"):
        tool_name = RichPrompt.ask("Tool name")
        selected_tool = next((t for t in tools if t.name == tool_name), None)
        if selected_tool:
            console.print(f"\n[bold]{selected_tool.name}[/bold]")
            console.print(f"Description: {selected_tool.description}")
            if selected_tool.inputSchema:
                console.print("\nParameters:")
                _print_schema(selected_tool.inputSchema)
        else:
            console.print(f"[red]Tool '{tool_name}' not found[/red]")


async def _interactive_list_prompts(client: Client[Any]) -> None:
    """Interactive prompt listing."""
    prompts = await client.list_prompts()

    table = Table(title="Available Prompts")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")

    for prompt in prompts:
        table.add_row(prompt.name, prompt.description or "No description")

    console.print(table)

    if Confirm.ask("\nView prompt details?"):
        prompt_name = RichPrompt.ask("Prompt name")
        selected_prompt = next((p for p in prompts if p.name == prompt_name), None)
        if selected_prompt:
            console.print(f"\n[bold]{selected_prompt.name}[/bold]")
            console.print(f"Description: {selected_prompt.description}")
            if selected_prompt.arguments:
                console.print("\nArguments:")
                for arg in selected_prompt.arguments:
                    required = "[red]required[/red]" if arg.required else "[green]optional[/green]"
                    console.print(f"  - {arg.name} ({required}): {arg.description}")
        else:
            console.print(f"[red]Prompt '{prompt_name}' not found[/red]")


async def _interactive_call_tool(client: Client[Any]) -> None:
    """Interactive tool execution."""
    tool_name = RichPrompt.ask("Tool name")
    tools = await client.list_tools()
    tool = next((t for t in tools if t.name == tool_name), None)

    if not tool:
        console.print(f"[red]Tool '{tool_name}' not found[/red]")
        return

    console.print(f"\nCalling tool: [bold]{tool.name}[/bold]")

    # Collect parameters
    arguments = {}
    if tool.inputSchema and "properties" in tool.inputSchema:
        properties = tool.inputSchema["properties"]
        required = tool.inputSchema.get("required", [])

        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get("type", "string")
            description = prop_schema.get("description", "")
            is_required = prop_name in required

            prompt_text = f"{prop_name} ({prop_type})"
            if description:
                prompt_text += f" - {description}"
            if is_required:
                prompt_text += " [required]"

            value = RichPrompt.ask(prompt_text, default="" if not is_required else None)

            if value:
                # Try to parse JSON for complex types
                if prop_type in ["object", "array"]:
                    try:
                        arguments[prop_name] = json.loads(value)
                    except json.JSONDecodeError:
                        console.print(f"[yellow]Warning: Invalid JSON for {prop_name}, using as string[/yellow]")
                        arguments[prop_name] = value
                elif prop_type == "boolean":
                    arguments[prop_name] = value.lower() in ["true", "yes", "1"]
                elif prop_type == "number":
                    try:
                        arguments[prop_name] = float(value)
                    except ValueError:
                        arguments[prop_name] = value
                elif prop_type == "integer":
                    try:
                        arguments[prop_name] = int(value)
                    except ValueError:
                        arguments[prop_name] = value
                else:
                    arguments[prop_name] = value

    # Execute tool
    console.print("\n[yellow]Executing tool...[/yellow]")
    try:
        result = await client.call_tool(tool_name, arguments)
        console.print("\n[green]Result:[/green]")
        print_json(data=result)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


async def _interactive_call_prompt(client: Client[Any]) -> None:
    """Interactive prompt execution."""
    prompt_name = RichPrompt.ask("Prompt name")
    prompts = await client.list_prompts()
    prompt = next((p for p in prompts if p.name == prompt_name), None)

    if not prompt:
        console.print(f"[red]Prompt '{prompt_name}' not found[/red]")
        return

    console.print(f"\nCalling prompt: [bold]{prompt.name}[/bold]")

    # Collect arguments
    arguments = {}
    if prompt.arguments:
        for arg in prompt.arguments:
            prompt_text = f"{arg.name}"
            if arg.description:
                prompt_text += f" - {arg.description}"
            if arg.required:
                prompt_text += " [required]"

            value = RichPrompt.ask(prompt_text, default="" if not arg.required else None)

            if value:
                # Try to parse JSON for complex values
                try:
                    arguments[arg.name] = json.loads(value)
                except json.JSONDecodeError:
                    arguments[arg.name] = value

    # Execute prompt
    console.print("\n[yellow]Executing prompt...[/yellow]")
    try:
        result = await client.get_prompt(prompt_name, arguments)
        console.print("\n[green]Result:[/green]")

        # Extract text content from messages
        for message in result.messages:
            if message.content and isinstance(message.content, TextContent):
                console.print(message.content.text)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")


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


def _parse_params(params: List[str]) -> Dict[str, Any]:
    """Parse command line parameters in format key=value."""
    result = {}
    for param in params:
        if "=" not in param:
            raise ValueError(f"Invalid parameter format: {param}. Expected key=value")

        key, value = param.split("=", 1)

        # Try to parse as JSON first
        try:
            result[key] = json.loads(value)
        except json.JSONDecodeError:
            # If not JSON, treat as string
            result[key] = value

    return result


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
