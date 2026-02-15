"""Domain models for conversation entities."""

from jean_michel.models.message import Actor, MessageCreate, MessageRecord
from jean_michel.models.metrics import CoverageRecord
from jean_michel.models.repository import (
    BranchRecord,
    CommitComparison,
    CommitDescriptor,
    CommitRefRecord,
    CompareFileRecord,
    RepositorySnapshot,
    TagRecord,
    WorktreeRecord,
)

__all__ = [
    "Actor",
    "MessageCreate",
    "MessageRecord",
    "CoverageRecord",
    "BranchRecord",
    "TagRecord",
    "WorktreeRecord",
    "RepositorySnapshot",
    "CommitRefRecord",
    "CommitDescriptor",
    "CompareFileRecord",
    "CommitComparison",
]
