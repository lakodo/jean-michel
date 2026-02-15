"""Metrics service layer."""

from __future__ import annotations

from pathlib import Path

from jean_michel.metrics import CoverageComputationError, compute_coverage_for_ref, resolve_ref_commit
from jean_michel.models import CoverageRecord
from jean_michel.settings import find_repo_root, get_coverage_command, get_repo_identity
from jean_michel.storage import DuckDBConversationStore


class MetricsService:
    """Compute and cache repository metrics."""

    def __init__(self, store: DuckDBConversationStore, repo_root: Path | None = None):
        self.store = store
        self.repo_root = repo_root or find_repo_root()
        self.repo_identity = get_repo_identity(self.repo_root)
        self._coverage_command_key = "coverage.command"

    def get_coverage_command(self) -> str:
        configured = self.store.get_repo_setting(self.repo_identity, self._coverage_command_key)
        return configured or get_coverage_command()

    def set_coverage_command(self, command: str) -> str:
        normalized = command.strip()
        if not normalized:
            raise ValueError("Coverage command cannot be empty")  # noqa: TRY003
        return self.store.set_repo_setting(self.repo_identity, self._coverage_command_key, normalized)

    def get_cached_coverage_for_ref(self, ref: str) -> CoverageRecord | None:
        commit_hash, _ = resolve_ref_commit(self.repo_root, ref)
        return self.store.get_coverage_report(self.repo_identity, commit_hash)

    def list_cached_coverages(self, limit: int = 2000) -> list[CoverageRecord]:
        return self.store.list_coverage_reports(self.repo_identity, limit=limit)

    def coverage_by_short_commit(self) -> dict[str, CoverageRecord]:
        reports = self.list_cached_coverages(limit=5000)
        mapping: dict[str, CoverageRecord] = {}
        for report in reports:
            mapping.setdefault(report.commit_short, report)
        return mapping

    def compute_coverage_for_ref(self, ref: str, force: bool = False) -> tuple[CoverageRecord, bool]:
        commit_hash, _ = resolve_ref_commit(self.repo_root, ref)
        existing = self.store.get_coverage_report(self.repo_identity, commit_hash)
        if existing and not force:
            return existing, True

        command = self.get_coverage_command()
        commit_hash, commit_short, line_rate, percentage = compute_coverage_for_ref(
            repo_root=self.repo_root,
            ref=ref,
            command=command,
        )

        stored = self.store.upsert_coverage_report(
            repo_identity=self.repo_identity,
            ref=ref,
            commit_hash=commit_hash,
            commit_short=commit_short,
            coverage_percent=percentage,
            line_rate=line_rate,
            command=command,
        )
        return stored, False


__all__ = ["CoverageComputationError", "MetricsService"]
