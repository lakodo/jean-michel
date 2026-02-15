"""MCP server exposing conversation operations."""

from __future__ import annotations

from typing import Literal

from mcp.server.fastmcp import FastMCP

from jean_michel.metrics import CoverageComputationError
from jean_michel.models import Actor, MessageRecord
from jean_michel.services import ConversationService, MetricsService
from jean_michel.settings import get_db_path
from jean_michel.storage import DuckDBConversationStore

Transport = Literal["stdio", "sse", "streamable-http"]


def _service() -> ConversationService:
    return ConversationService(DuckDBConversationStore(get_db_path()))


def _metrics() -> MetricsService:
    return MetricsService(DuckDBConversationStore(get_db_path()))


def _serialize_message(message: MessageRecord) -> dict[str, str | int]:
    return {
        "id": message.id,
        "content": message.content,
        "actor_name": message.actor_name,
        "actor_email": message.actor_email,
        "created_at": message.created_at.isoformat(),
    }


def create_mcp_server(host: str = "127.0.0.1", port: int = 8001) -> FastMCP:
    """Create the MCP server for conversation operations."""

    server = FastMCP(
        name="jean-michel-conversation",
        instructions="Conversation-only MCP server for Jean-Michel.",
        host=host,
        port=port,
    )

    @server.tool()
    def list_messages(limit: int = 100) -> list[dict[str, str | int]]:
        """List recent conversation messages."""

        return [_serialize_message(message) for message in _service().list_messages(limit=limit)]

    @server.tool()
    def send_message(
        content: str,
        actor_name: str | None = None,
        actor_email: str | None = None,
    ) -> dict[str, str | int]:
        """Send a conversation message.

        If actor_name and actor_email are not provided, git identity is used.
        """

        actor: Actor | None = None
        if actor_name or actor_email:
            if not actor_name or not actor_email:
                raise ValueError("actor_name and actor_email must be provided together")
            actor = Actor(name=actor_name, email=actor_email)

        created = _service().send_message(content=content, actor=actor)
        return _serialize_message(created)

    @server.tool()
    def get_default_actor() -> dict[str, str]:
        """Return the default actor resolved from git/environment."""

        actor = _service().default_actor()
        return {"name": actor.name, "email": actor.email}

    @server.tool()
    def get_coverage(ref: str) -> dict[str, str | int | float | bool]:
        """Get cached coverage for a reference if available."""

        try:
            report = _metrics().get_cached_coverage_for_ref(ref)
        except CoverageComputationError as exc:
            return {"found": False, "error": str(exc)}

        if report is None:
            return {"found": False}

        return {
            "found": True,
            "id": report.id,
            "repo_identity": report.repo_identity,
            "ref": report.ref,
            "commit_hash": report.commit_hash,
            "commit_short": report.commit_short,
            "coverage_percent": report.coverage_percent,
            "line_rate": report.line_rate,
            "command": report.command,
            "created_at": report.created_at.isoformat(),
        }

    @server.tool()
    def compute_coverage(ref: str, force: bool = False) -> dict[str, str | int | float | bool]:
        """Compute and store coverage for a reference."""

        report, cached = _metrics().compute_coverage_for_ref(ref=ref, force=force)
        return {
            "cached": cached,
            "id": report.id,
            "repo_identity": report.repo_identity,
            "ref": report.ref,
            "commit_hash": report.commit_hash,
            "commit_short": report.commit_short,
            "coverage_percent": report.coverage_percent,
            "line_rate": report.line_rate,
            "command": report.command,
            "created_at": report.created_at.isoformat(),
        }

    @server.tool()
    def get_coverage_command() -> dict[str, str]:
        """Return current configured coverage command for this repository."""

        return {"command": _metrics().get_coverage_command()}

    @server.tool()
    def set_coverage_command(command: str) -> dict[str, str]:
        """Update coverage command for this repository."""

        return {"command": _metrics().set_coverage_command(command)}

    return server


def run_mcp_server(
    transport: Transport = "stdio",
    host: str = "127.0.0.1",
    port: int = 8001,
) -> None:
    """Run the conversation MCP server."""

    server = create_mcp_server(host=host, port=port)
    server.run(transport=transport)
