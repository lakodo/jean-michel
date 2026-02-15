"""Git identity helpers."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from jean_michel.models import Actor
from jean_michel.settings import find_repo_root


class GitIdentityError(RuntimeError):
    """Raised when git identity cannot be resolved."""


def _git_config_value(key: str, cwd: Path) -> str | None:
    try:
        value = subprocess.check_output(  # noqa: S603
            ["git", "config", "--get", key],  # noqa: S607
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    return value or None


def resolve_default_actor(start: Path | None = None) -> Actor:
    """Resolve default actor from environment then git config."""

    env_name = os.getenv("GIT_AUTHOR_NAME") or os.getenv("JM_ACTOR_NAME")
    env_email = os.getenv("GIT_AUTHOR_EMAIL") or os.getenv("JM_ACTOR_EMAIL")
    if env_name and env_email:
        return Actor(name=env_name, email=env_email)

    repo_root = find_repo_root(start)
    name = _git_config_value("user.name", repo_root)
    email = _git_config_value("user.email", repo_root)

    if not name or not email:
        msg = "Unable to resolve actor identity from git config or JM_ACTOR_* environment variables"
        raise GitIdentityError(msg)

    return Actor(name=name, email=email)
