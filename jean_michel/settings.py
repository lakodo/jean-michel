"""Application settings and path resolution."""

from __future__ import annotations

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


def get_db_path() -> Path:
    """Return DuckDB path and ensure parent directory exists."""

    env_path = os.getenv("JEAN_MICHEL_DB_PATH")
    if env_path:
        path = Path(env_path).expanduser().resolve()
    else:
        path = find_repo_root() / ".jean-michel" / "conversation.duckdb"

    path.parent.mkdir(parents=True, exist_ok=True)
    return path
