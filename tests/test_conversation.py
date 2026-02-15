from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

import jean_michel.cli as cli_module
from jean_michel.cli import app
from jean_michel.services import ConversationService
from jean_michel.storage import DuckDBConversationStore


def test_conversation_service_send_and_list(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("JM_ACTOR_NAME", "Test User")
    monkeypatch.setenv("JM_ACTOR_EMAIL", "test@example.com")

    db_path = tmp_path / "conversation.duckdb"
    service = ConversationService(DuckDBConversationStore(db_path))

    created = service.send_message("hello world")

    assert created.id >= 1
    assert created.actor_name == "Test User"
    assert created.actor_email == "test@example.com"

    messages = service.list_messages()
    assert len(messages) == 1
    assert messages[0].content == "hello world"


def test_cli_send_and_list_alias(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("JM_ACTOR_NAME", "Cli User")
    monkeypatch.setenv("JM_ACTOR_EMAIL", "cli@example.com")
    monkeypatch.setenv("JEAN_MICHEL_DB_PATH", str(tmp_path / "conversation.duckdb"))

    runner = CliRunner()

    send_result = runner.invoke(app, ["send", "what's up?"])
    assert send_result.exit_code == 0
    assert "Cli User <cli@example.com>" in send_result.stdout

    list_alias_result = runner.invoke(app, ["lm"])
    assert list_alias_result.exit_code == 0
    assert "what's up?" in list_alias_result.stdout

    list_subcommand_result = runner.invoke(app, ["list", "messages"])
    assert list_subcommand_result.exit_code == 0
    assert "what's up?" in list_subcommand_result.stdout


def test_cli_mcp_without_subcommand_starts_server(monkeypatch):
    captured: dict[str, object] = {}

    def fake_run_mcp_server(transport: str, host: str, port: int) -> None:
        captured["transport"] = transport
        captured["host"] = host
        captured["port"] = port

    monkeypatch.setattr(cli_module, "run_mcp_server", fake_run_mcp_server)
    runner = CliRunner()

    result = runner.invoke(app, ["mcp"])

    assert result.exit_code == 0
    assert captured == {"transport": "stdio", "host": "127.0.0.1", "port": 8001}


def test_cli_no_args_shows_help():
    runner = CliRunner()

    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Jean-Michel conversation CLI" in result.stdout
    assert "Usage:" in result.stdout
