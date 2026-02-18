from core.batch_processor import run_batch_from_file
from harvest.src.core.job_result import HarvestJobResult
from datetime import datetime


def test_run_batch_from_file_runs_each_domain(tmp_path, monkeypatch):
    domains_file = tmp_path / "domains.txt"
    domains_file.write_text("example.com\nexample.org\n")

    calls = []

    now = datetime.now()

    def fake_run(domain, **kwargs):
        calls.append(domain)
        return HarvestJobResult(
            domain=domain,
            sources=["google"],
            limit=10,
            started_at=now,
            finished_at=now,
            status="success",
            raw_output_path=None,
            error_message=None,
        )

    monkeypatch.setattr("core.batch_processor.run_harvest_job", fake_run)

    results = run_batch_from_file(str(domains_file), sources=["google"], limit=10, output_base=tmp_path)

    assert len(calls) == 2
    assert all(r.status == "success" for r in results)


def test_run_batch_from_file_skips_empty_and_comments(tmp_path, monkeypatch):
    domains_file = tmp_path / "domains.txt"
    domains_file.write_text("#comment\nexample.com\n\n# ignore\nexample.org\n")

    calls = []

    now = datetime.now()

    def fake_run(domain, **kwargs):
        calls.append(domain)
        return HarvestJobResult(
            domain=domain,
            sources=["google"],
            limit=10,
            started_at=now,
            finished_at=now,
            status="success",
            raw_output_path=None,
            error_message=None,
        )

    monkeypatch.setattr("core.batch_processor.run_harvest_job", fake_run)

    run_batch_from_file(str(domains_file), output_base=tmp_path)

    assert calls == ["example.com", "example.org"]


def test_run_batch_from_file_runs_all_even_if_failure(tmp_path, monkeypatch):
    domains_file = tmp_path / "domains.txt"
    domains_file.write_text("example.com\nfail.com\nexample.org\n")

    now = datetime.now()

    def fake_run(domain, **kwargs):
        if domain == "fail.com":
            return HarvestJobResult(domain, ["google"], 10, now, now, "error", None, "fail")
        return HarvestJobResult(domain, ["google"], 10, now, now, "success", None, None)

    monkeypatch.setattr("core.batch_processor.run_harvest_job", fake_run)

    results = run_batch_from_file(str(domains_file), output_base=tmp_path)
    assert len(results) == 3
    statuses = [r.status for r in results]
    assert statuses == ["success", "error", "success"]
