"""Git repository inspection helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from jean_michel.models import BranchRecord, RepositorySnapshot, TagRecord, WorktreeRecord


def _run_git(args: list[str], repo_root: Path) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=repo_root, text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError("Git command failed") from exc


def _parse_branch_lines(raw: str) -> list[BranchRecord]:
    result: list[BranchRecord] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        name, commit, date, subject = (line.split("|", maxsplit=3) + ["", "", "", ""])[:4]
        result.append(BranchRecord(name=name, commit=commit, date=date, subject=subject))
    return result


def _parse_tag_lines(raw: str) -> list[TagRecord]:
    result: list[TagRecord] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        name, commit, date = (line.split("|", maxsplit=2) + ["", "", ""])[:3]
        result.append(TagRecord(name=name, commit=commit, date=date))
    return result


def parse_worktree_porcelain(raw: str) -> list[WorktreeRecord]:
    """Parse `git worktree list --porcelain` output."""

    blocks = [block for block in raw.strip().split("\n\n") if block.strip()]
    result: list[WorktreeRecord] = []

    for block in blocks:
        path = ""
        head = ""
        branch: str | None = None
        detached = False
        for line in block.splitlines():
            if line.startswith("worktree "):
                path = line.removeprefix("worktree ").strip()
            elif line.startswith("HEAD "):
                head = line.removeprefix("HEAD ").strip()[:12]
            elif line.startswith("branch "):
                branch_ref = line.removeprefix("branch ").strip()
                branch = branch_ref.removeprefix("refs/heads/")
            elif line.strip() == "detached":
                detached = True

        if path:
            result.append(WorktreeRecord(path=path, head=head, branch=branch, detached=detached))

    return result


def inspect_repository(repo_root: Path) -> RepositorySnapshot:
    """Collect branch/tag/worktree state for a repository."""

    local_raw = _run_git(
        [
            "for-each-ref",
            "refs/heads",
            "--sort=-committerdate",
            "--format=%(refname:short)|%(objectname:short)|%(committerdate:short)|%(subject)",
        ],
        repo_root,
    )
    remote_raw = _run_git(
        [
            "for-each-ref",
            "refs/remotes",
            "--sort=-committerdate",
            "--format=%(refname:short)|%(objectname:short)|%(committerdate:short)|%(subject)",
        ],
        repo_root,
    )
    tags_raw = _run_git(
        [
            "for-each-ref",
            "refs/tags",
            "--sort=-creatordate",
            "--format=%(refname:short)|%(objectname:short)|%(creatordate:short)",
        ],
        repo_root,
    )
    worktrees_raw = _run_git(["worktree", "list", "--porcelain"], repo_root)

    return RepositorySnapshot(
        local_branches=_parse_branch_lines(local_raw),
        remote_branches=_parse_branch_lines(remote_raw),
        tags=_parse_tag_lines(tags_raw),
        worktrees=parse_worktree_porcelain(worktrees_raw),
    )
