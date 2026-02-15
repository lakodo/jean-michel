from __future__ import annotations

from pathlib import Path

import pytest

import jean_michel.services.metrics as metrics_service_module
from jean_michel.metrics.coverage import parse_coverage_xml
from jean_michel.services.metrics import MetricsService
from jean_michel.storage import DuckDBConversationStore


def test_parse_coverage_xml(tmp_path: Path):
    coverage_file = tmp_path / "coverage.xml"
    coverage_file.write_text('<coverage line-rate="0.875"></coverage>')

    line_rate, percentage = parse_coverage_xml(coverage_file)

    assert line_rate == 0.875
    assert percentage == 87.5


def test_metrics_service_compute_and_cache(tmp_path: Path, monkeypatch):
    store = DuckDBConversationStore(tmp_path / "storage.duckdb")

    monkeypatch.setattr(metrics_service_module, "resolve_ref_commit", lambda repo_root, ref: ("abc123", "abc123"))
    monkeypatch.setattr(metrics_service_module, "get_coverage_command", lambda: "fake-cmd")

    state = {"calls": 0}

    def fake_compute(repo_root, ref, command):
        state["calls"] += 1
        return ("abc123", "abc123", 0.82, 82.0)

    monkeypatch.setattr(metrics_service_module, "compute_coverage_for_ref", fake_compute)

    service = MetricsService(store=store, repo_root=tmp_path / "repo-demo")

    report, cached = service.compute_coverage_for_ref("main")
    assert cached is False
    assert report.coverage_percent == 82.0

    report_cached, cached_again = service.compute_coverage_for_ref("main")
    assert cached_again is True
    assert report_cached.id == report.id
    assert state["calls"] == 1

    got = service.get_cached_coverage_for_ref("main")
    assert got is not None
    assert got.commit_hash == "abc123"


def test_metrics_service_coverage_command_setting(tmp_path: Path, monkeypatch):
    store = DuckDBConversationStore(tmp_path / "storage.duckdb")
    service = MetricsService(store=store, repo_root=tmp_path / "repo-demo")

    monkeypatch.setattr(metrics_service_module, "get_coverage_command", lambda: "default-cmd")

    assert service.get_coverage_command() == "default-cmd"

    saved = service.set_coverage_command("uv run pytest --cov --cov-report=xml")
    assert saved == "uv run pytest --cov --cov-report=xml"
    assert service.get_coverage_command() == "uv run pytest --cov --cov-report=xml"

    with pytest.raises(ValueError):
        service.set_coverage_command("  ")
