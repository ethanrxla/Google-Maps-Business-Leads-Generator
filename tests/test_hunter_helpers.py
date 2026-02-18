import types

from leadgen.integrations import hunter_client


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}

    def json(self):
        return self._json


def test_hunter_domain_search_builds_url(monkeypatch):
    called = {}

    def fake_get(url, params=None, timeout=None):
        called["url"] = url
        called["params"] = params
        return DummyResponse(200, {"data": {"emails": []}})

    monkeypatch.setattr("requests.get", fake_get)
    client = hunter_client.HunterClient(api_key="key", base_url="https://api.hunter.test")
    res = hunter_client.hunter_domain_search("example.com", client=client, limit=3)
    assert res is not None
    assert called["url"] == "https://api.hunter.test/domain-search"
    assert called["params"]["domain"] == "example.com"
    assert called["params"]["limit"] == 3
    assert called["params"]["api_key"] == "key"


def test_hunter_email_finder_handles_non_200(monkeypatch):
    monkeypatch.setattr("requests.get", lambda *a, **k: DummyResponse(500, {}))
    client = hunter_client.HunterClient(api_key="key", base_url="https://api.hunter.test")
    res = hunter_client.hunter_email_finder("example.com", "Jane", "Doe", client=client)
    assert res is None
