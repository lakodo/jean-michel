from __future__ import annotations

from pathlib import Path

from jean_michel.settings import get_default_api_port


def test_default_api_port_is_deterministic_for_same_repo(tmp_path: Path):
    repo_dir = tmp_path / "repo-alpha"
    repo_dir.mkdir()

    first = get_default_api_port(start=repo_dir)
    second = get_default_api_port(start=repo_dir)

    assert first == second
    assert 5600 <= first <= 6599


def test_default_api_port_can_be_overridden(monkeypatch):
    monkeypatch.setenv("JEAN_MICHEL_API_PORT", "7777")

    assert get_default_api_port() == 7777
