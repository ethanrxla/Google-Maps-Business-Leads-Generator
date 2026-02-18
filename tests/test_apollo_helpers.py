from leadgen.integrations import apollo_client


class DummyResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json


def test_apollo_bulk_org_enrich_builds_request(monkeypatch):
    called = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        called["url"] = url
        called["headers"] = headers
        called["json"] = json
        return DummyResponse(200, {"organizations": [{"domain": "example.com", "name": "Example"}]})

    monkeypatch.setattr("requests.post", fake_post)
    client = apollo_client.ApolloClient(api_key="key", base_url="https://api.apollo.test")
    res = apollo_client.apollo_bulk_org_enrich(["example.com"], client=client)
    assert "example.com" in res
    assert called["url"] == "https://api.apollo.test/organizations/bulk_enrich"
    assert called["json"]["domains"] == ["example.com"]
    assert called["headers"]["X-Api-Key"] == "key"


def test_apollo_job_postings_handles_non_200(monkeypatch):
    monkeypatch.setattr("requests.get", lambda *a, **k: DummyResponse(500, {}))
    client = apollo_client.ApolloClient(api_key="key", base_url="https://api.apollo.test")
    res = apollo_client.apollo_get_org_job_postings("org123", client=client)
    assert res is None
