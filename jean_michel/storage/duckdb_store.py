"""DuckDB-backed conversation store."""

from __future__ import annotations

from pathlib import Path

import duckdb

from jean_michel.models import MessageCreate, MessageRecord


class DuckDBConversationStore:
    """Persist conversation messages in DuckDB."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path))

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("CREATE SEQUENCE IF NOT EXISTS messages_id_seq START 1")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGINT PRIMARY KEY DEFAULT nextval('messages_id_seq'),
                    content TEXT NOT NULL,
                    actor_name TEXT NOT NULL,
                    actor_email TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT now()
                )
                """
            )

    def insert_message(self, message: MessageCreate) -> MessageRecord:
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO messages (content, actor_name, actor_email)
                VALUES (?, ?, ?)
                RETURNING id, content, actor_name, actor_email, created_at
                """,
                [message.content, message.actor.name, message.actor.email],
            ).fetchone()

        return MessageRecord(
            id=row[0],
            content=row[1],
            actor_name=row[2],
            actor_email=row[3],
            created_at=row[4],
        )

    def list_messages(self, limit: int = 100) -> list[MessageRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, content, actor_name, actor_email, created_at
                FROM messages
                ORDER BY id DESC
                LIMIT ?
                """,
                [limit],
            ).fetchall()

        return [
            MessageRecord(
                id=row[0],
                content=row[1],
                actor_name=row[2],
                actor_email=row[3],
                created_at=row[4],
            )
            for row in rows
        ]
