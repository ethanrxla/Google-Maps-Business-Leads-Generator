import json
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient

import backend.server as server
import backend.stripe_utils as stripe_utils
from leadgen.generator import make_pack_id
from leadgen.packs_index import build_packs_index, resolve_pack_files


class DummyStripeSession:
    def __init__(self, url):
        self.url = url


def test_build_packs_index_and_resolve(tmp_path: Path):
    base = tmp_path / "packs"
    pack_dir = base / "usa" / "florida" / "boca_raton" / "restaurants"
    pack_dir.mkdir(parents=True)
    csv_path = pack_dir / "restaurants.csv"
    jsonl_path = pack_dir / "restaurants.jsonl"
    csv_path.write_text("name,website\n", encoding="utf-8")
    jsonl_path.write_text("{}", encoding="utf-8")

    index = build_packs_index(base)
    pack_id = "usa/florida/boca_raton/restaurants"
    assert pack_id in index
    assert index[pack_id]["csv"] == csv_path
    assert index[pack_id]["jsonl"] == jsonl_path
    assert "usa_florida_boca_raton_restaurants" in index

    resolved_csv, resolved_jsonl = resolve_pack_files(pack_id, base)
    assert resolved_csv == csv_path
    assert resolved_jsonl == jsonl_path


def test_create_checkout_session_handler(monkeypatch, tmp_path):
    pack_dir = tmp_path / "packs" / "usa"
    pack_dir.mkdir(parents=True)
    csv_path = pack_dir / "leads.csv"
    csv_path.write_text("name\n", encoding="utf-8")

    # Ensure resolve_pack_files points at tmp_path
    monkeypatch.setattr(server, "resolve_pack_files", lambda pack_id: (csv_path, None))

    created = {}

    class FakeStripe:
        class checkout:
            class Session:
                @staticmethod
                def create(**kwargs):
                    created["metadata"] = kwargs.get("metadata")
                    return DummyStripeSession(url="https://stripe.test/checkout")

        class Webhook:
            @staticmethod
            def construct_event(payload, sig_header, secret=None):
                return {}

    monkeypatch.setattr(stripe_utils, "stripe", FakeStripe)
    monkeypatch.setattr(stripe_utils.config, "stripe_secret_key", "sk_test")
    monkeypatch.setattr(stripe_utils.config, "stripe_price_id", "price_123")
    monkeypatch.setattr(stripe_utils.config, "frontend_base_url", "https://frontend.test")

    body = {"pack_id": "usa", "success_url": "https://ok", "cancel_url": "https://cancel"}
    result = server.create_checkout_session_handler(body)

    assert result["url"] == "https://stripe.test/checkout"
    assert created["metadata"]["pack_id"] == "usa"


def test_webhook_handler_delivers(monkeypatch, tmp_path):
    csv_path = tmp_path / "packs" / "usa" / "file.csv"
    csv_path.parent.mkdir(parents=True)
    csv_path.write_text("name\n", encoding="utf-8")
    jsonl_path = csv_path.with_suffix(".jsonl")
    jsonl_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(server, "resolve_pack_files", lambda pack_id: (csv_path, jsonl_path))

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"pack_id": "usa/file"},
            }
        },
    }

    monkeypatch.setattr(stripe_utils, "verify_webhook_signature", lambda payload, sig: event)

    payload = b"{}"
    sig_header = "t=123"
    result = server.webhook_handler(payload, sig_header)

    assert result["status"] == "delivered"
    assert "csv" in result and "jsonl" in result


def _setup_fake_stripe_retrieve(monkeypatch, session_data):
    class FakeStripe:
        class checkout:
            class Session:
                @staticmethod
                def retrieve(session_id):
                    return session_data

        class Webhook:
            @staticmethod
            def construct_event(payload, sig_header, secret=None):
                return {}

    monkeypatch.setattr(stripe_utils, "stripe", FakeStripe)
    monkeypatch.setattr(stripe_utils, "_require_stripe", lambda: None)
    monkeypatch.setattr(stripe_utils.config, "stripe_secret_key", "sk_test")


def test_download_pack_success_csv(monkeypatch, tmp_path):
    csv_path = tmp_path / "packs" / "restaurants_boca_raton_fl.csv"
    csv_path.parent.mkdir(parents=True)
    csv_path.write_text("name\n", encoding="utf-8")
    jsonl_path = csv_path.with_suffix(".jsonl")
    jsonl_path.write_text("{}", encoding="utf-8")

    _setup_fake_stripe_retrieve(
        monkeypatch,
        {
            "id": "cs_test_123",
            "payment_status": "paid",
            "metadata": {"pack_id": "restaurants_boca_raton_fl"},
        },
    )

    def fake_resolve(pack_id, base_dir=Path("data/packs")):
        return csv_path, jsonl_path

    monkeypatch.setattr(server, "resolve_pack_files", fake_resolve)

    client = TestClient(server.app)
    resp = client.get("/download-pack", params={"session_id": "cs_test_123", "format": "csv"})

    assert resp.status_code == 200
    assert "restaurants_boca_raton_fl.csv" in resp.headers.get("content-disposition", "")
    assert resp.text == "name\n"


def test_download_pack_unpaid_session(monkeypatch, tmp_path):
    _setup_fake_stripe_retrieve(
        monkeypatch,
        {
            "id": "cs_test_123",
            "payment_status": "unpaid",
            "metadata": {"pack_id": "restaurants_boca_raton_fl"},
        },
    )
    monkeypatch.setattr(server, "resolve_pack_files", lambda pack_id, base_dir=Path("data/packs"): (None, None))

    client = TestClient(server.app)
    resp = client.get("/download-pack", params={"session_id": "cs_test_123", "format": "csv"})

    assert resp.status_code == 402


def test_download_pack_missing_pack_id(monkeypatch):
    _setup_fake_stripe_retrieve(
        monkeypatch,
        {
            "id": "cs_test_123",
            "payment_status": "paid",
            "metadata": {},
        },
    )
    client = TestClient(server.app)
    resp = client.get("/download-pack", params={"session_id": "cs_test_123", "format": "csv"})
    assert resp.status_code == 400


def test_download_pack_file_not_found(monkeypatch, tmp_path):
    _setup_fake_stripe_retrieve(
        monkeypatch,
        {
            "id": "cs_test_123",
            "payment_status": "paid",
            "metadata": {"pack_id": "restaurants_boca_raton_fl"},
        },
    )

    def fake_resolve(pack_id, base_dir=Path("data/packs")):
        return tmp_path / "missing.csv", tmp_path / "missing.jsonl"

    monkeypatch.setattr(server, "resolve_pack_files", fake_resolve)

    client = TestClient(server.app)
    resp = client.get("/download-pack", params={"session_id": "cs_test_123", "format": "csv"})
    assert resp.status_code == 404


def test_download_pack_invalid_format(monkeypatch, tmp_path):
    _setup_fake_stripe_retrieve(
        monkeypatch,
        {
            "id": "cs_test_123",
            "payment_status": "paid",
            "metadata": {"pack_id": "restaurants_boca_raton_fl"},
        },
    )
    monkeypatch.setattr(server, "resolve_pack_files", lambda *args, **kwargs: (tmp_path / "file.csv", tmp_path / "file.jsonl"))

    client = TestClient(server.app)
    resp = client.get("/download-pack", params={"session_id": "cs_test_123", "format": "pdf"})
    assert resp.status_code == 400


def test_start_pack_creates_checkout_session_and_returns_url(monkeypatch):
    created = {}

    def fake_create_checkout_session(pack_id, price_id, success_url, cancel_url):
        created["pack_id"] = pack_id
        created["success_url"] = success_url
        created["cancel_url"] = cancel_url
        return {"url": "https://example.com/checkout"}

    def fake_generate_pack(**kwargs):
        return {"pack_id": kwargs["pack_id"], "sellable": True}

    monkeypatch.setattr("leadgen.generator.generate_pack", fake_generate_pack)
    monkeypatch.setattr(stripe_utils, "create_checkout_session", fake_create_checkout_session)
    monkeypatch.setattr(stripe_utils.config, "frontend_base_url", "https://frontend.test")
    monkeypatch.setattr(stripe_utils.config, "stripe_price_id", "price_123")

    client = TestClient(server.app)
    payload = {
        "query": "restaurants in Boca Raton, FL",
        "country": "usa",
        "state": "florida",
        "city": "boca raton",
        "niche": "restaurants",
        "limit": 50,
    }
    resp = client.post("/start-pack", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    expected_pack_id = make_pack_id("usa", "florida", None, "boca raton", "restaurants", 50)
    assert data["pack_id"] == expected_pack_id
    assert data["checkout_url"] == "https://example.com/checkout"
    assert created["pack_id"] == expected_pack_id


def test_start_pack_rejects_invalid_payload(monkeypatch):
    client = TestClient(server.app)
    resp = client.post("/start-pack", json={"country": "usa"})
    assert resp.status_code == 422


def test_start_pack_rejects_unsellable_pack_and_surfaces_gate_reasons(monkeypatch):
    def fake_generate_pack(**kwargs):
        return {
            "pack_id": kwargs["pack_id"],
            "sellable": False,
            "quality_gate_failures": [
                "email_coverage 20% < 70% (2/10)",
                "phone_coverage 10% < 75% (1/10)",
            ],
        }

    monkeypatch.setattr("leadgen.generator.generate_pack", fake_generate_pack)
    monkeypatch.setattr(stripe_utils.config, "frontend_base_url", "https://frontend.test")

    client = TestClient(server.app)
    payload = {
        "query": "restaurants in Boca Raton, FL",
        "country": "usa",
        "state": "florida",
        "city": "boca raton",
        "niche": "restaurants",
        "limit": 10,
    }
    resp = client.post("/start-pack", json=payload)
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "not sellable" in detail
    assert "email_coverage" in detail
    assert "phone_coverage" in detail
