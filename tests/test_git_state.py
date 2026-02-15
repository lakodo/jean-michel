from __future__ import annotations

from pathlib import Path

import jean_michel.git_state as git_state
from jean_michel.git_state import inspect_repository, parse_worktree_porcelain


def test_parse_worktree_porcelain():
    raw = """worktree /tmp/repo
HEAD 0123456789abcdef
branch refs/heads/main

worktree /tmp/repo-wt
HEAD fedcba9876543210
detached
"""

    parsed = parse_worktree_porcelain(raw)

    assert len(parsed) == 2
    assert parsed[0].path == "/tmp/repo"
    assert parsed[0].head == "0123456789ab"
    assert parsed[0].branch == "main"
    assert parsed[0].detached is False
    assert parsed[1].detached is True
    assert parsed[1].branch is None


def test_inspect_repository(monkeypatch):
    outputs = {
        "for-each-ref refs/heads --sort=-committerdate --format=%(refname:short)|%(objectname:short)|%(committerdate:short)|%(subject)": "main|abc1234|2026-02-15|init\n",
        "for-each-ref refs/remotes --sort=-committerdate --format=%(refname:short)|%(objectname:short)|%(committerdate:short)|%(subject)": "origin/main|abc1234|2026-02-15|init\n",
        "for-each-ref refs/tags --sort=-creatordate --format=%(refname:short)|%(objectname:short)|%(creatordate:short)": "v0.1.0|abc1234|2026-02-15\n",
        "worktree list --porcelain": "worktree /tmp/repo\nHEAD abcdef0123456789\nbranch refs/heads/main\n",
    }

    def fake_run_git(args: list[str], repo_root: Path) -> str:
        key = " ".join(args)
        return outputs[key]

    monkeypatch.setattr(git_state, "_run_git", fake_run_git)

    snapshot = inspect_repository(Path("/tmp/repo"))

    assert snapshot.local_branches[0].name == "main"
    assert snapshot.remote_branches[0].name == "origin/main"
    assert snapshot.tags[0].name == "v0.1.0"
    assert snapshot.worktrees[0].branch == "main"
