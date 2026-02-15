from __future__ import annotations

from pathlib import Path

import jean_michel.git_state as git_state
from jean_michel.git_state import compare_refs, inspect_repository, list_reference_candidates, parse_worktree_porcelain


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
    assert parsed[0].path == "/tmp/repo"  # noqa: S108
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

    snapshot = inspect_repository(Path("/tmp/repo"))  # noqa: S108

    assert snapshot.local_branches[0].name == "main"
    assert snapshot.remote_branches[0].name == "origin/main"
    assert snapshot.tags[0].name == "v0.1.0"
    assert snapshot.worktrees[0].branch == "main"


def test_list_reference_candidates(monkeypatch):
    outputs = {
        "for-each-ref refs/heads refs/remotes refs/tags --sort=-committerdate --format=%(refname:short)": "main\norigin/main\nv0.1.0\n",
        "log -n200 --pretty=format:%h": "abc1234\ndef5678\n",
    }

    def fake_run_git(args: list[str], repo_root: Path) -> str:
        return outputs[" ".join(args)]

    monkeypatch.setattr(git_state, "_run_git", fake_run_git)

    refs = list_reference_candidates(Path("/tmp/repo"))  # noqa: S108
    assert [ref.name for ref in refs] == ["main", "origin/main", "v0.1.0", "abc1234", "def5678"]

    filtered = list_reference_candidates(Path("/tmp/repo"), query="abc")  # noqa: S108
    assert [ref.name for ref in filtered] == ["abc1234"]


def test_compare_refs(monkeypatch):
    outputs = {
        "show -s --format=%H|%h|%cs|%s main": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa|aaaaaaa|2026-02-15|main head\n",
        "show -s --format=%H|%h|%cs|%s feature": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb|bbbbbbb|2026-02-16|feature head\n",
        "rev-list --count aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa..bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb": "3\n",
        "rev-list --count bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb..aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": "1\n",
        "diff --numstat aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb": "5\t2\tapp.py\n3\t0\tREADME.md\n-\t-\tbinary.png\n",
    }

    def fake_run_git(args: list[str], repo_root: Path) -> str:
        key = " ".join(args)
        return outputs[key]

    monkeypatch.setattr(git_state, "_run_git", fake_run_git)

    result = compare_refs(Path("/tmp/repo"), "main", "feature")  # noqa: S108

    assert result.base.ref == "main"
    assert result.target.ref == "feature"
    assert result.ahead_count == 3
    assert result.behind_count == 1
    assert result.files_changed == 3
    assert result.total_additions == 8
    assert result.total_deletions == 2
    assert result.files[0].path == "app.py"
