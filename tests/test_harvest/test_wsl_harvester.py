import sys
import pytest

from core import wsl_harvester
from core.wsl_harvester import run_harvest_job


def test_run_harvester_uses_params(mock_subprocess_run, temp_output_dir):
    # Use run_harvest_job to avoid heavy WSL setup
    result = run_harvest_job(
        domain="example.com",
        sources=["duckduckgo"],
        limit=10,
        output_base=temp_output_dir,
        runner=lambda *args, **kwargs: type("P", (), {"returncode": 0, "stdout": "data", "stderr": ""})(),
    )

    assert result.status == "success"
    assert "example_com" in (result.raw_output_path or "")


def test_cli_parses_sources_and_limit(monkeypatch):
    recorded = {}

    def fake_run(domain, sources, limit, output_base=None, **kwargs):
        recorded["domain"] = domain
        recorded["sources"] = sources
        recorded["limit"] = limit
        from core.job_result import HarvestJobResult
        now = wsl_harvester.datetime.now()
        return HarvestJobResult(
            domain=domain,
            sources=sources,
            limit=limit,
            started_at=now,
            finished_at=now,
            status="success",
            raw_output_path=None,
            error_message=None,
            parsed_data={},
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(wsl_harvester, "run_harvest_job", fake_run)

    argv = ["prog", "-d", "example.com", "-s", "google,bing", "-l", "123"]
    monkeypatch.setattr(sys, "argv", argv)
    wsl_harvester.main()

    assert recorded["domain"] == "example.com"
    assert recorded["sources"] == ["google", "bing"]
    assert recorded["limit"] == 123
