import pytest

from backend.coinbase_payments import create_coinbase_charge


class DummyResponse:
    def __init__(self, status_code=201, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json


def test_coinbase_create_charge_success(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResponse(201, {"data": {"hosted_url": "https://cb.com/host", "id": "charge_1"}})

    monkeypatch.setattr("requests.post", fake_post)
    res = create_coinbase_charge("prod", 10, {})
    assert res["hosted_url"] == "https://cb.com/host"
    assert res["charge_id"] == "charge_1"


def test_coinbase_create_charge_failure(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResponse(400, text="bad")

    monkeypatch.setattr("requests.post", fake_post)
    res = create_coinbase_charge("prod", 10, {})
    assert "error" in res
