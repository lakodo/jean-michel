"""DuckDB-backed conversation store."""

from __future__ import annotations

from pathlib import Path

import duckdb

from jean_michel.models import CoverageRecord, MessageCreate, MessageRecord


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
            conn.execute("CREATE SEQUENCE IF NOT EXISTS coverage_reports_id_seq START 1")
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS repo_settings (
                    repo_identity TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT now(),
                    UNIQUE(repo_identity, key)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS coverage_reports (
                    id BIGINT PRIMARY KEY DEFAULT nextval('coverage_reports_id_seq'),
                    repo_identity TEXT NOT NULL,
                    ref TEXT NOT NULL,
                    commit_hash TEXT NOT NULL,
                    commit_short TEXT NOT NULL,
                    coverage_percent DOUBLE NOT NULL,
                    line_rate DOUBLE NOT NULL,
                    command TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT now(),
                    UNIQUE(repo_identity, commit_hash)
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

    @staticmethod
    def _coverage_from_row(row: tuple) -> CoverageRecord:
        return CoverageRecord(
            id=row[0],
            repo_identity=row[1],
            ref=row[2],
            commit_hash=row[3],
            commit_short=row[4],
            coverage_percent=float(row[5]),
            line_rate=float(row[6]),
            command=row[7],
            created_at=row[8],
        )

    def get_coverage_report(self, repo_identity: str, commit_hash: str) -> CoverageRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, repo_identity, ref, commit_hash, commit_short, coverage_percent, line_rate, command, created_at
                FROM coverage_reports
                WHERE repo_identity = ? AND commit_hash = ?
                """,
                [repo_identity, commit_hash],
            ).fetchone()

        return self._coverage_from_row(row) if row else None

    def list_coverage_reports(self, repo_identity: str, limit: int = 1000) -> list[CoverageRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, repo_identity, ref, commit_hash, commit_short, coverage_percent, line_rate, command, created_at
                FROM coverage_reports
                WHERE repo_identity = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [repo_identity, limit],
            ).fetchall()

        return [self._coverage_from_row(row) for row in rows]

    def upsert_coverage_report(
        self,
        repo_identity: str,
        ref: str,
        commit_hash: str,
        commit_short: str,
        coverage_percent: float,
        line_rate: float,
        command: str,
    ) -> CoverageRecord:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO coverage_reports (
                    repo_identity, ref, commit_hash, commit_short, coverage_percent, line_rate, command
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(repo_identity, commit_hash) DO UPDATE SET
                    ref = excluded.ref,
                    commit_short = excluded.commit_short,
                    coverage_percent = excluded.coverage_percent,
                    line_rate = excluded.line_rate,
                    command = excluded.command,
                    created_at = now()
                """,
                [repo_identity, ref, commit_hash, commit_short, coverage_percent, line_rate, command],
            )
            row = conn.execute(
                """
                SELECT id, repo_identity, ref, commit_hash, commit_short, coverage_percent, line_rate, command, created_at
                FROM coverage_reports
                WHERE repo_identity = ? AND commit_hash = ?
                """,
                [repo_identity, commit_hash],
            ).fetchone()

        return self._coverage_from_row(row)

    def get_repo_setting(self, repo_identity: str, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT value
                FROM repo_settings
                WHERE repo_identity = ? AND key = ?
                """,
                [repo_identity, key],
            ).fetchone()
        return row[0] if row else None

    def set_repo_setting(self, repo_identity: str, key: str, value: str) -> str:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO repo_settings (repo_identity, key, value)
                VALUES (?, ?, ?)
                ON CONFLICT(repo_identity, key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = now()
                """,
                [repo_identity, key, value],
            )
            row = conn.execute(
                """
                SELECT value
                FROM repo_settings
                WHERE repo_identity = ? AND key = ?
                """,
                [repo_identity, key],
            ).fetchone()

        return row[0]
