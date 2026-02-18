"""Tests for pipeline endpoints in backend/server.py.

Uses TestClient + monkeypatch for isolated handler/route testing.
"""

import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient

import backend.server as server


@pytest.fixture
def client():
    return TestClient(server.app)


class TestPipelineBatchRoute:
    def test_success(self, client, monkeypatch):
        monkeypatch.setattr(
            server, "pipeline_batch_handler",
            lambda payload: {
                "batch_id": "b1",
                "status": "completed",
                "candidates_collected": 5,
                "candidates_kept": 4,
                "verified_count": 4,
                "pack": {"pack_id": "p1", "sellable": True},
            },
        )

        resp = client.post("/pipeline/batch", json={
            "query": "dentists Miami",
            "city": "Miami",
            "state": "FL",
            "niche": "dentists",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["batch_id"] == "b1"
        assert data["status"] == "completed"

    def test_missing_required_field(self, client):
        resp = client.post("/pipeline/batch", json={"city": "Miami"})
        assert resp.status_code == 422  # Pydantic validation

    def test_handler_error(self, client, monkeypatch):
        monkeypatch.setattr(
            server, "pipeline_batch_handler",
            lambda payload: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        resp = client.post("/pipeline/batch", json={
            "query": "test",
            "city": "Miami",
        })
        assert resp.status_code == 500


class TestPipelineBatchStatusRoute:
    def test_found(self, client, monkeypatch):
        monkeypatch.setattr(
            server, "pipeline_batch_status_handler",
            lambda batch_id: {
                "id": batch_id,
                "status": "completed",
                "batch_type": "city_sweep",
            },
        )

        resp = client.get("/pipeline/batch/b1")
        assert resp.status_code == 200
        assert resp.json()["id"] == "b1"

    def test_not_found(self, client, monkeypatch):
        from fastapi import HTTPException

        def _raise_404(batch_id):
            raise HTTPException(status_code=404, detail="Batch not found")

        monkeypatch.setattr(
            server, "pipeline_batch_status_handler", _raise_404,
        )

        resp = client.get("/pipeline/batch/missing")
        assert resp.status_code == 404


class TestPipelineStatsRoute:
    def test_success(self, client, monkeypatch):
        monkeypatch.setattr(
            server, "pipeline_stats_handler",
            lambda: {
                "total_candidates": 100,
                "total_verified": 80,
                "sellable_packs": 5,
            },
        )

        resp = client.get("/pipeline/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_candidates"] == 100
        assert data["total_verified"] == 80
        assert data["sellable_packs"] == 5
