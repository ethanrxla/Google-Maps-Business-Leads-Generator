import pytest

from leadgen.integrations.hunter_client import HunterClient
from leadgen.integrations.apollo_client import ApolloClient
from leadgen.enrichment import LeadEnricher
from leadgen.models import Business, LeadResult, WebsiteAnalysis


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}

    def json(self):
        return self._json


def _analysis():
    return WebsiteAnalysis(
        has_website=True,
        needs_website=False,
        needs_redesign=False,
        needs_chatbot=False,
        needs_ai_integration=False,
        raw_data={},
    )


def _lead(email=None, website="https://example.com"):
    return LeadResult(
        business=Business(name="Biz", address="Addr", website=website, email=email, place_id=None),
        analysis=_analysis(),
    )


def test_hunter_rate_limit_sleep(monkeypatch):
    times = {"now": 0.0, "sleeps": []}

    def fake_time():
        return times["now"]

    def fake_sleep(seconds):
        times["sleeps"].append(seconds)
        times["now"] += seconds

    monkeypatch.setattr("leadgen.integrations.hunter_client.time.time", fake_time)
    monkeypatch.setattr("leadgen.integrations.hunter_client.time.sleep", fake_sleep)
    monkeypatch.setattr("requests.get", lambda *a, **k: DummyResponse(200, {"ok": True}))

    client = HunterClient(api_key="key", rate_limit_seconds=1.0)
    client.domain_search("example.com")
    times["now"] += 0.25  # call again before rate_limit_seconds has elapsed
    client.domain_search("example.com")

    assert times["sleeps"] == [0.75]


def test_hunter_handles_429_rate_limit(monkeypatch):
    resp = DummyResponse(429, {"errors": ["rate limit"]}, headers={"Retry-After": "2"})
    monkeypatch.setattr("requests.get", lambda *a, **k: resp)

    client = HunterClient(api_key="key")
    res = client.domain_search("example.com")
    assert res["error"]
    assert res.get("rate_limited") is True
    assert res.get("retry_after") == 2


def test_apollo_handles_429_rate_limit(monkeypatch):
    resp = DummyResponse(429, {"error": "rate limit"}, headers={"Retry-After": "1"})
    monkeypatch.setattr("requests.post", lambda *a, **k: resp)

    client = ApolloClient(api_key="key")
    res = client.enrich_person_by_email("a@example.com")
    assert res["error"]
    assert res.get("rate_limited") is True
    assert res.get("retry_after") == 1


def test_enricher_bubbles_rate_limit_errors_without_crashing(monkeypatch):
    class RLHunter:
        def domain_search(self, domain, limit=5):
            return {"error": "status 429", "rate_limited": True}

        def verify_email(self, email):
            return {"error": "status 429", "rate_limited": True}

    class RLApollo:
        def enrich_person_by_email(self, email):
            return {"error": "status 429", "rate_limited": True}

        def enrich_company_by_domain(self, domain):
            return {"error": "status 429", "rate_limited": True}

    lead = _lead(email=None, website="https://example.com")
    enricher = LeadEnricher(apollo_client=RLApollo(), hunter_client=RLHunter())

    enricher.enrich_lead(lead)

    assert lead.business.email is None  # no new email chosen
    assert "hunter" in lead.enrichment
    assert "apollo" in lead.enrichment
    assert lead.enrichment["hunter"]["rate_limited"] is True
    assert lead.enrichment["apollo"]["rate_limited"] is True
