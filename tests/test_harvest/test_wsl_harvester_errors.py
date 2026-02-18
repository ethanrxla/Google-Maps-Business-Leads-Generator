import subprocess

from core.wsl_harvester import run_harvest_job


def test_run_harvest_job_handles_missing_binary(tmp_path):
    def fake_runner(*args, **kwargs):
        raise FileNotFoundError("missing")

    res = run_harvest_job(
        domain="example.com",
        sources=["google"],
        limit=5,
        output_base=tmp_path,
        runner=fake_runner,
    )
    assert res.status == "error"
    assert "not found" in (res.error_message or "")


def test_run_harvest_job_handles_timeout(tmp_path):
    def fake_runner(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="theHarvester", timeout=1)

    res = run_harvest_job(
        domain="example.com",
        sources=["google"],
        limit=5,
        output_base=tmp_path,
        runner=fake_runner,
    )
    assert res.status == "error"
    assert "timed out" in (res.error_message or "")


def test_run_harvest_job_handles_generic_exception(tmp_path):
    def fake_runner(*args, **kwargs):
        raise RuntimeError("boom")

    res = run_harvest_job(
        domain="example.com",
        sources=["google"],
        limit=5,
        output_base=tmp_path,
        runner=fake_runner,
    )
    assert res.status == "error"
    assert "boom" in (res.error_message or "")
