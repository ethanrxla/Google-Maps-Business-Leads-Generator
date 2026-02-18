import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient

import backend.server as server


def test_harvest_domain_success(monkeypatch, tmp_path):
    now = server.datetime.now()

    def fake_run(domain, sources, limit, output_base, export_windows=False, runner=None, **kwargs):      
        return server.HarvestJobResult(
            domain=domain,
            sources=sources,
            limit=limit,
            started_at=now,
            finished_at=now,
            status="success",
            raw_output_path=str(tmp_path / "raw.txt"),
            error_message=None,
            stdout="out",
            stderr="",
        )

    monkeypatch.setattr(server, "run_harvest_job", fake_run)

    client = TestClient(server.app)
    payload = {"domain": "example.com", "sources": ["google"], "limit": 50}
    resp = client.post("/harvest-domain", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["domain"] == "example.com"
    assert data["status"] == "completed"
    assert data["raw_output_path"]
    assert data["lines_in_raw"] == 0
    assert data["stdout"] == "out"


def test_harvest_domain_invalid(monkeypatch):
    client = TestClient(server.app)
    resp = client.post("/harvest-domain", json={"domain": ""})
    assert resp.status_code in (400, 422)


def test_harvest_domain_failure(monkeypatch):
    now = server.datetime.now()

    def fake_run(*args, **kwargs):
        return server.HarvestJobResult(
            domain="example.com",
            sources=["google"],
            limit=10,
            started_at=now,
            finished_at=now,
            status="error",
            raw_output_path=None,
            error_message="boom",
            stdout=None,
            stderr=None,
        )

    monkeypatch.setattr(server, "run_harvest_job", fake_run)
    client = TestClient(server.app)
    resp = client.post("/harvest-domain", json={"domain": "example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "error"
    assert data["error_message"] == "boom"
    assert "stdout" in data
