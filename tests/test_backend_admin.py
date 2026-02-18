import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient

import backend.server as server
from leadgen.packs_index import list_packs


def test_list_packs_helper(tmp_path):
    base = tmp_path / "data" / "packs"
    pack_dir = base / "usa" / "florida" / "boca_raton"
    pack_dir.mkdir(parents=True)
    csv_file = pack_dir / "restaurants_20.csv"
    csv_file.write_text("name\n", encoding="utf-8")
    jsonl_file = csv_file.with_suffix(".jsonl")
    jsonl_file.write_text("{}", encoding="utf-8")

    packs = list_packs(base)
    assert len(packs) == 1
    pack = packs[0]
    assert pack["pack_id"] == "usa_florida_boca_raton"
    assert pack["csv_path"].endswith("restaurants_20.csv")
    assert pack["jsonl_path"].endswith("restaurants_20.jsonl")


def test_admin_list_packs_endpoint(monkeypatch):
    sample = [
        {"pack_id": "sample_pack", "csv_path": "data/packs/sample.csv", "jsonl_path": None}
    ]

    monkeypatch.setattr(server, "list_packs", lambda: sample)

    client = TestClient(server.app)
    resp = client.get("/admin/packs")
    assert resp.status_code == 200
    data = resp.json()
    assert "packs" in data
    assert data["packs"] == sample
