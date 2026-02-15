"""Git repository inspection helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from jean_michel.models import (
    BranchRecord,
    CommitComparison,
    CommitDescriptor,
    CommitRefRecord,
    CompareFileRecord,
    RepositorySnapshot,
    TagRecord,
    WorktreeRecord,
)


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


def list_reference_candidates(
    repo_root: Path,
    max_commits: int = 200,
    query: str | None = None,
    limit: int = 50,
) -> list[CommitRefRecord]:
    """Return reference candidates for compare inputs."""

    refs_raw = _run_git(
        [
            "for-each-ref",
            "refs/heads",
            "refs/remotes",
            "refs/tags",
            "--sort=-committerdate",
            "--format=%(refname:short)",
        ],
        repo_root,
    )
    commits_raw = _run_git(
        [
            "log",
            f"-n{max_commits}",
            "--pretty=format:%h",
        ],
        repo_root,
    )

    normalized_query = (query or "").strip().lower()
    seen: set[str] = set()
    result: list[CommitRefRecord] = []

    for value in [*refs_raw.splitlines(), *commits_raw.splitlines()]:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        if normalized_query and normalized_query not in normalized.lower():
            continue
        seen.add(normalized)
        result.append(CommitRefRecord(name=normalized))
        if len(result) >= limit:
            break

    return result


def _resolve_commit(repo_root: Path, ref: str) -> CommitDescriptor:
    normalized_ref = ref.strip()
    if not normalized_ref:
        raise ValueError("Reference cannot be empty")

    raw = _run_git(
        [
            "show",
            "-s",
            "--format=%H|%h|%cs|%s",
            normalized_ref,
        ],
        repo_root,
    ).strip()

    full_hash, short_hash, date, subject = (raw.split("|", maxsplit=3) + ["", "", "", ""])[:4]
    return CommitDescriptor(
        ref=normalized_ref,
        full_hash=full_hash,
        short_hash=short_hash,
        date=date,
        subject=subject,
    )


def compare_refs(repo_root: Path, base_ref: str, target_ref: str) -> CommitComparison:
    """Compare two references by commit hash/branch/tag."""

    base = _resolve_commit(repo_root, base_ref)
    target = _resolve_commit(repo_root, target_ref)

    ahead_count_raw = _run_git(["rev-list", "--count", f"{base.full_hash}..{target.full_hash}"], repo_root).strip()
    behind_count_raw = _run_git(["rev-list", "--count", f"{target.full_hash}..{base.full_hash}"], repo_root).strip()
    numstat_raw = _run_git(["diff", "--numstat", base.full_hash, target.full_hash], repo_root)

    files: list[CompareFileRecord] = []
    total_additions = 0
    total_deletions = 0

    for line in numstat_raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        raw_additions, raw_deletions, path = parts[0], parts[1], parts[2]
        additions = int(raw_additions) if raw_additions.isdigit() else 0
        deletions = int(raw_deletions) if raw_deletions.isdigit() else 0
        total_additions += additions
        total_deletions += deletions
        files.append(CompareFileRecord(path=path, additions=additions, deletions=deletions))

    return CommitComparison(
        base=base,
        target=target,
        ahead_count=int(ahead_count_raw or "0"),
        behind_count=int(behind_count_raw or "0"),
        files_changed=len(files),
        total_additions=total_additions,
        total_deletions=total_deletions,
        files=files,
    )
