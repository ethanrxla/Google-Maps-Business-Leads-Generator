from pathlib import Path

from core.export_manager import (
    export_raw_results_to_csv,
    export_structured_results_to_json,
)
from core.job_result import HarvestJobResult
from datetime import datetime


def test_export_raw_results_to_csv(tmp_path):
    now = datetime.now()
    raw_jobs = [
        HarvestJobResult(
            domain="example.com",
            sources=["google"],
            limit=5,
            started_at=now,
            finished_at=now,
            status="success",
            raw_output_path=str(tmp_path / "a.txt"),
            error_message=None,
        ),
        HarvestJobResult(
            domain="example.org",
            sources=["google"],
            limit=5,
            started_at=now,
            finished_at=now,
            status="error",
            raw_output_path=None,
            error_message="fail",
        ),
    ]
    tmp_path.joinpath("a.txt").write_text("line1\nline2\n")
    out_csv = tmp_path / "out.csv"
    export_raw_results_to_csv(raw_jobs, str(out_csv))
    content = out_csv.read_text().strip().splitlines()
    assert content[0].split(",")[0] == "domain"
    assert len(content) == 3  # header + 2 rows


def test_export_structured_results_to_json(tmp_path):
    now = datetime.now()
    results = [
        HarvestJobResult(
            domain="example.com",
            sources=["google"],
            limit=5,
            started_at=now,
            finished_at=now,
            status="success",
            raw_output_path=None,
            error_message=None,
        ),
        HarvestJobResult(
            domain="example.org",
            sources=["google"],
            limit=5,
            started_at=now,
            finished_at=now,
            status="success",
            raw_output_path=None,
            error_message=None,
        ),
    ]
    out_json = tmp_path / "out.json"
    export_structured_results_to_json(results, str(out_json))
    data = out_json.read_text()
    assert "example.com" in data
    assert "lines_in_raw" in data


def test_export_handles_empty_job_list(tmp_path):
    out_csv = tmp_path / "empty.csv"
    out_json = tmp_path / "empty.json"
    export_raw_results_to_csv([], str(out_csv))
    export_structured_results_to_json([], str(out_json))
    assert out_csv.exists()
    assert out_json.exists()
