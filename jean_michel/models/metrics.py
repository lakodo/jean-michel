"""Metric models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CoverageRecord(BaseModel):
    """Stored coverage measurement for a specific commit."""

    id: int
    repo_identity: str
    ref: str
    commit_hash: str
    commit_short: str
    coverage_percent: float
    line_rate: float
    command: str
    created_at: datetime
