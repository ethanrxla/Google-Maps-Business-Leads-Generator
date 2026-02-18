import pytest

from leadgen.integrations.hunter_client import HunterClient


class DummyResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json


def test_hunter_domain_search_success(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return DummyResponse(200, {"data": {"domain": params.get("domain"), "emails": []}})

    monkeypatch.setattr("requests.get", fake_get)
    client = HunterClient(api_key="test")
    res = client.domain_search("example.com", limit=3)
    assert res["data"]["domain"] == "example.com"


def test_hunter_handles_non_200(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return DummyResponse(429, {"errors": ["rate limit"]})

    monkeypatch.setattr("requests.get", fake_get)
    client = HunterClient(api_key="test")
    res = client.domain_search("example.com", limit=3)
    assert "error" in res


def test_hunter_handles_bad_json(monkeypatch):
    class Bad:
        status_code = 200

        def json(self):
            raise ValueError("bad json")

    monkeypatch.setattr("requests.get", lambda *a, **k: Bad())
    client = HunterClient(api_key="test")
    res = client.verify_email("a@example.com")
    assert "error" in res
