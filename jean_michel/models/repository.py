"""Repository inspection models."""

from __future__ import annotations

from pydantic import BaseModel


class BranchRecord(BaseModel):
    """Git branch record."""

    name: str
    commit: str
    date: str
    subject: str


class TagRecord(BaseModel):
    """Git tag record."""

    name: str
    commit: str
    date: str


class WorktreeRecord(BaseModel):
    """Git worktree record."""

    path: str
    head: str
    branch: str | None = None
    detached: bool = False


class RepositorySnapshot(BaseModel):
    """Repository metadata displayed in UI."""

    local_branches: list[BranchRecord]
    remote_branches: list[BranchRecord]
    tags: list[TagRecord]
    worktrees: list[WorktreeRecord]
