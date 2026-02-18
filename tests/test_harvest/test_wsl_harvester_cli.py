from pathlib import Path

from core.wsl_harvester import (
    build_theharvester_command,
    run_harvest_job,
    parse_theharvester_output,
)
from core.job_result import HarvestJobResult


def test_build_theharvester_command_basic():
    cfg = {"theharvester": {"output_base_path": "/tmp/out/raw_leads/example"}}
    cmd = build_theharvester_command(
        domain="example.com",
        sources=["google", "bing"],
        limit=100,
        config=cfg,
    )
    joined = " ".join(cmd)
    assert "theHarvester" in cmd[0]
    assert "-d" in cmd and "example.com" in cmd
    assert "-l" in cmd and "100" in cmd
    assert "google,bing" in joined
    assert "/tmp/out/raw_leads/example" in joined


def test_build_theharvester_command_export_windows_flag():
    cfg = {"theharvester": {"output_base_path": "/tmp/out/raw_leads/example"}}
    cmd = build_theharvester_command(
        domain="example.com",
        sources=["google"],
        limit=10,
        config=cfg,
    )
    assert "-d" in cmd
    assert isinstance(cmd, list)


def test_run_harvest_job_returns_metadata_fields(tmp_path):
    class Dummy:
        def __init__(self):
            self.returncode = 0
            self.stdout = "info@example.com\nHost: api.example.com"
            self.stderr = ""

    result = run_harvest_job(
        domain="example.com",
        sources=["google", "bing"],
        limit=10,
        output_base=tmp_path,
        runner=lambda *a, **k: Dummy(),
    )

    assert result.domain == "example.com"
    assert result.sources == ["google", "bing"]
    assert result.limit == 10
    assert result.status == "success"
    assert result.started_at is not None
    assert result.finished_at is not None
    assert result.error_message is None
    assert result.parsed_data.get("emails")


def test_run_harvest_job_uses_runner(tmp_path):
    calls = []

    class Dummy:
        def __init__(self):
            self.returncode = 0
            self.stdout = "RESULTS"
            self.stderr = ""

    def fake_runner(cmd, capture_output, text, timeout, env=None):
        calls.append(cmd)
        return Dummy()

    result = run_harvest_job(
        domain="example.com",
        sources=["google"],
        limit=5,
        output_base=tmp_path,
        runner=fake_runner,
    )

    assert hasattr(result, "status")
    assert result.status == "success"
    assert result.raw_output_path
    assert Path(result.raw_output_path).exists()
    assert calls, "runner was not invoked"


def test_parse_theharvester_output_basic():
    text = Path(__file__).parent / "fixtures" / "theharvester_output_example.txt"
    parsed = parse_theharvester_output(text.read_text())
    assert "info@example.com" in parsed["emails"]
    assert any("example.com" in h for h in parsed["hosts"])
