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
        path = find_repo_root() / ".jean-michel" / "conversation.duckdb"

    path.parent.mkdir(parents=True, exist_ok=True)
    return path
