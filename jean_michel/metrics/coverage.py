"""Coverage computation for repository commits."""

from __future__ import annotations

import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


class CoverageComputationError(RuntimeError):
    """Raised when commit coverage cannot be computed."""


def _coverage_env() -> dict[str, str]:
    """Return subprocess environment for coverage commands.

    Worktree execution should not inherit an unrelated active virtualenv
    from the caller shell (common with uv users).
    """

    env = dict(os.environ)
    env.pop("VIRTUAL_ENV", None)
    return env


def _run_git(args: list[str], repo_root: Path) -> str:
    try:
        return subprocess.check_output(  # noqa: S603
            ["git", *args],  # noqa: S607
            cwd=repo_root,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise CoverageComputationError("Git command failed while computing coverage") from exc  # noqa: TRY003


def resolve_ref_commit(repo_root: Path, ref: str) -> tuple[str, str]:
    """Resolve a ref to full and short commit hashes."""

    normalized = ref.strip()
    if not normalized:
        raise CoverageComputationError("Reference cannot be empty")  # noqa: TRY003

    full_hash = _run_git(["rev-parse", normalized], repo_root)
    short_hash = _run_git(["rev-parse", "--short=7", normalized], repo_root)
    return full_hash, short_hash


def parse_coverage_xml(path: Path) -> tuple[float, float]:
    """Return (line_rate, percentage) from a coverage.xml file."""

    if not path.exists():
        raise CoverageComputationError("coverage.xml not found after test command")  # noqa: TRY003

    try:
        root = ET.parse(path).getroot()  # noqa: S314
        line_rate = float(root.attrib["line-rate"])
    except (ET.ParseError, KeyError, ValueError) as exc:
        raise CoverageComputationError("Unable to parse coverage.xml") from exc  # noqa: TRY003

    percentage = round(line_rate * 100, 2)
    return line_rate, percentage


def compute_coverage_for_ref(
    repo_root: Path,
    ref: str,
    command: str,
) -> tuple[str, str, float, float]:
    """Compute coverage for a specific ref in an isolated temporary worktree.

    Returns: (commit_hash, commit_short, line_rate, coverage_percent)
    """

    commit_hash, commit_short = resolve_ref_commit(repo_root, ref)

    with tempfile.TemporaryDirectory(prefix="jm-cov-") as tmp_dir:
        worktree_path = Path(tmp_dir)
        try:
            subprocess.check_call(  # noqa: S603
                ["git", "worktree", "add", "--detach", str(worktree_path), commit_hash],  # noqa: S607
                cwd=repo_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise CoverageComputationError("Unable to create temporary worktree for coverage") from exc  # noqa: TRY003

        try:
            process = subprocess.run(  # noqa: S602
                command,
                cwd=worktree_path,
                shell=True,
                text=True,
                capture_output=True,
                env=_coverage_env(),
                check=False,
            )
            if process.returncode != 0:
                error_msg = (process.stderr or process.stdout or "Coverage command failed").strip()
                raise CoverageComputationError(error_msg[:800])

            line_rate, percentage = parse_coverage_xml(worktree_path / "coverage.xml")
            return commit_hash, commit_short, line_rate, percentage
        finally:
            subprocess.run(  # noqa: S603
                ["git", "worktree", "remove", "--force", str(worktree_path)],  # noqa: S607
                cwd=repo_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
