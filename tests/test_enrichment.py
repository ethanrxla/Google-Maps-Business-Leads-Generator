from leadgen.enrichment import LeadEnricher
from leadgen.models import Business, LeadResult, WebsiteAnalysis


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
    biz = Business(name="Biz", address="Addr", website=website, email=email, place_id=None)
    return LeadResult(business=biz, analysis=_analysis())


def test_enrich_lead_calls_apollo_and_hunter_when_email_present():
    calls = {"apollo_person": 0, "apollo_org": 0, "hunter_verify": 0}

    class FakeApollo:
        def enrich_person_by_email(self, email):
            calls["apollo_person"] += 1
            return {"person": {"email": email, "title": "CEO"}}

        def enrich_company_by_domain(self, domain):
            calls["apollo_org"] += 1
            return {"organization": {"domain": domain}}

    class FakeHunter:
        def verify_email(self, email):
            calls["hunter_verify"] += 1
            return {"result": "deliverable", "email": email}

        def domain_search(self, domain, limit=5):
            raise AssertionError("domain_search should not be called when email present")

    lead = _lead(email="a@example.com")
    enricher = LeadEnricher(apollo_client=FakeApollo(), hunter_client=FakeHunter())

    enricher.enrich_lead(lead)

    assert calls["apollo_person"] == 1
    assert calls["hunter_verify"] == 1
    assert lead.enrichment["apollo"]["person"]["email"] == "a@example.com"
    assert lead.enrichment["hunter"]["result"] == "deliverable"
    # Company enrichment should run when a domain is present
    assert calls["apollo_org"] == 1


def test_enrich_lead_uses_hunter_domain_email_and_verifies(monkeypatch):
    calls = {"domain": 0, "verify": 0, "apollo_person": 0, "apollo_org": 0}

    class FakeHunter:
        def domain_search(self, domain, limit=5):
            calls["domain"] += 1
            return {
                "data": {
                    "emails": [
                        {"value": "info@example.com", "confidence": 95},
                        {"value": "support@example.com", "confidence": 80},
                    ]
                }
            }

        def verify_email(self, email):
            calls["verify"] += 1
            return {"result": "deliverable", "email": email}

    class FakeApollo:
        def enrich_person_by_email(self, email):
            calls["apollo_person"] += 1
            return {"person": {"email": email, "title": "Founder"}}

        def enrich_company_by_domain(self, domain):
            calls["apollo_org"] += 1
            return {"organization": {"domain": domain, "name": "Example Co"}}

    lead = _lead(email=None, website="https://example.com")
    enricher = LeadEnricher(apollo_client=FakeApollo(), hunter_client=FakeHunter())

    enricher.enrich_lead(lead)

    assert lead.business.email == "info@example.com"
    assert lead.business.email_source == "hunter_domain_search"
    assert calls["domain"] == 1
    assert calls["verify"] == 1  # newly found email should be verified
    assert calls["apollo_person"] == 1  # new email should trigger person enrichment
    assert calls["apollo_org"] == 1  # domain should trigger organization enrichment
    assert lead.enrichment["hunter"]["result"] == "deliverable"
    assert lead.enrichment["apollo"]["organization"]["name"] == "Example Co"
