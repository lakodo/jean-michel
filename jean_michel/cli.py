"""Typer CLI for Jean-Michel conversation MVP."""

from __future__ import annotations

import typer

from jean_michel.mcp_server import run_mcp_server
from jean_michel.services import ConversationService
from jean_michel.settings import get_db_path
from jean_michel.storage import DuckDBConversationStore

app = typer.Typer(help="Jean-Michel conversation CLI")
list_app = typer.Typer(help="List entities")
mcp_app = typer.Typer(help="MCP server commands")
app.add_typer(list_app, name="list")
app.add_typer(mcp_app, name="mcp")


def _service() -> ConversationService:
    return ConversationService(DuckDBConversationStore(get_db_path()))


@app.callback(invoke_without_command=True)
def app_callback(ctx: typer.Context) -> None:
    """Show help when no command is provided."""

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


@app.command("send")
def send_message(content: str) -> None:
    """Send a message using default git identity."""

    message = _service().send_message(content=content)
    typer.echo(f"[{message.id}] {message.display_actor}")
    typer.echo(message.content)


def _print_messages(limit: int) -> None:
    messages = _service().list_messages(limit=limit)
    if not messages:
        typer.echo("No messages")
        return

    for message in messages:
        typer.echo(f"[{message.id}] {message.created_at} {message.display_actor}")
        typer.echo(f"  {message.content}")


def _start_mcp_server(transport: str, host: str, port: int) -> None:
    valid_transports = {"stdio", "sse", "streamable-http"}
    normalized_transport = transport.strip().lower()
    if normalized_transport not in valid_transports:
        raise typer.BadParameter("transport must be one of: stdio, sse, streamable-http")

    typer.echo(f"Starting MCP server with transport={normalized_transport}")
    run_mcp_server(transport=normalized_transport, host=host, port=port)


@list_app.command("messages")
def list_messages(limit: int = typer.Option(100, min=1, help="Maximum number of messages")) -> None:
    """List conversation messages."""

    _print_messages(limit)


@app.command("list-messages")
def list_messages_alias(limit: int = typer.Option(100, min=1, help="Maximum number of messages")) -> None:
    """Alias for `list messages`."""

    _print_messages(limit)


@app.command("lm")
def list_messages_short_alias(limit: int = typer.Option(100, min=1, help="Maximum number of messages")) -> None:
    """Short alias for message listing."""

    _print_messages(limit)


@mcp_app.callback(invoke_without_command=True)
def mcp_default(
    ctx: typer.Context,
    transport: str = typer.Option("stdio", help="Transport: stdio, sse, or streamable-http"),
    host: str = typer.Option("127.0.0.1", help="Bind host for HTTP transports"),
    port: int = typer.Option(8001, help="Bind port for HTTP transports"),
) -> None:
    """Start MCP server when no subcommand is provided."""

    if ctx.invoked_subcommand is not None:
        return

    _start_mcp_server(transport=transport, host=host, port=port)


@mcp_app.command("serve")
def mcp_serve(
    transport: str = typer.Option("stdio", help="Transport: stdio, sse, or streamable-http"),
    host: str = typer.Option("127.0.0.1", help="Bind host for HTTP transports"),
    port: int = typer.Option(8001, help="Bind port for HTTP transports"),
) -> None:
    """Start the MCP server exposing conversation operations."""
    _start_mcp_server(transport=transport, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    app()
