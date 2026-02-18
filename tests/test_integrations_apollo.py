import pytest

from leadgen.integrations.apollo_client import ApolloClient


class DummyResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json


def test_apollo_enrich_person_success(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResponse(200, {"person": {"email": json.get("email")}})

    monkeypatch.setattr("requests.post", fake_post)
    client = ApolloClient(api_key="test")
    res = client.enrich_person_by_email("a@example.com")
    assert res.get("person", {}).get("email") == "a@example.com"


def test_apollo_handles_non_200(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResponse(401, {"error": "unauthorized"})

    monkeypatch.setattr("requests.post", fake_post)
    client = ApolloClient(api_key="test")
    res = client.enrich_person_by_email("a@example.com")
    assert "error" in res


def test_apollo_handles_bad_json(monkeypatch):
    class Bad:
        status_code = 200

        def json(self):
            raise ValueError("bad")

    monkeypatch.setattr("requests.post", lambda *a, **k: Bad())
    client = ApolloClient(api_key="test")
    res = client.enrich_company_by_domain("example.com")
    assert "error" in res
