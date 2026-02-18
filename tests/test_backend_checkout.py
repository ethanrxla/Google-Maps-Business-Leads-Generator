import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient

import backend.server as server


def test_calculate_cart_line_items_discounts():
    items = [
        {"pack_id": "p1", "enrichment_tier": "basic", "quantity": 1},
        {"pack_id": "p2", "enrichment_tier": "basic", "quantity": 1},
        {"pack_id": "p3", "enrichment_tier": "basic", "quantity": 1},
    ]
    line_items = server.calculate_cart_line_items(items)
    assert len(line_items) == 3
    assert line_items[2]["price_data"]["unit_amount"] == int(server.BASE_PRICE_BASIC * 0.5)


def test_create_cart_checkout_session(monkeypatch):
    created = {}

    class FakeStripe:
        class checkout:
            class Session:
                @staticmethod
                def create(**kwargs):
                    created.update(kwargs)
                    return {"url": "https://stripe.test/checkout", "id": "sess_123"}

    monkeypatch.setattr(server.stripe_utils, "stripe", FakeStripe)
    monkeypatch.setattr(server.config, "frontend_base_url", "https://frontend.test")
    monkeypatch.setattr(server, "calculate_cart_line_items", lambda items: [{"test": "item"}])

    client = TestClient(server.app)
    payload = {"items": [{"pack_id": "p1", "enrichment_tier": "basic", "quantity": 1}]}
    resp = client.post("/create-cart-checkout", json=payload)
    assert resp.status_code == 200
    assert "checkout_url" in resp.json()
    assert created.get("line_items")[0]["test"] == "item"
