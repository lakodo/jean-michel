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


class CommitRefRecord(BaseModel):
    """Resolvable git reference shown in UI suggestions."""

    name: str


class CommitDescriptor(BaseModel):
    """Resolved commit metadata."""

    ref: str
    full_hash: str
    short_hash: str
    date: str
    subject: str


class CompareFileRecord(BaseModel):
    """File-level diff stats between two refs."""

    path: str
    additions: int
    deletions: int


class CommitComparison(BaseModel):
    """Comparison result between two refs."""

    base: CommitDescriptor
    target: CommitDescriptor
    ahead_count: int
    behind_count: int
    files_changed: int
    total_additions: int
    total_deletions: int
    files: list[CompareFileRecord]
