"""Application settings and path resolution."""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Resolve git repository root from a starting directory."""

    cwd = start or Path.cwd()
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return Path(output)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return cwd


def _git_value(args: list[str], cwd: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_repo_identity(start: Path | None = None) -> str:
    """Return a stable repository identity string used for defaults."""

    repo_root = find_repo_root(start)
    remote_url = _git_value(["remote", "get-url", "origin"], cwd=repo_root)
    if remote_url:
        return remote_url
    return repo_root.name


def get_default_api_port(start: Path | None = None) -> int:
    """Return deterministic default API port for a repository."""

    env_port = os.getenv("JEAN_MICHEL_API_PORT")
    if env_port:
        return int(env_port)

    identity = get_repo_identity(start)
    digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 1000
    return 5600 + bucket


def get_db_path() -> Path:
    """Return DuckDB path and ensure parent directory exists."""

    env_path = os.getenv("JEAN_MICHEL_DB_PATH")
    if env_path:
        path = Path(env_path).expanduser().resolve()
    else:
        repo_root = find_repo_root()
        storage_dir = repo_root / ".jean-michel"
        new_path = storage_dir / "storage.duckdb"
        legacy_path = storage_dir / "conversation.duckdb"
        if not new_path.exists() and legacy_path.exists():
            legacy_path.rename(new_path)
        path = new_path

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_coverage_command() -> str:
    """Return command used to compute coverage in target repositories."""

    return os.getenv("JEAN_MICHEL_COVERAGE_CMD", "uv run pytest --cov --cov-report=xml")
