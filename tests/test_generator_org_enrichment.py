from pathlib import Path

from leadgen.generator import generate_pack
from leadgen.models import Business, WebsiteAnalysis


class DummyAnalysis(WebsiteAnalysis):
    def __init__(self):
        super().__init__(
            has_website=True,
            needs_website=False,
            needs_redesign=False,
            needs_chatbot=False,
            needs_ai_integration=False,
            raw_data={},
        )


def _lead(domain="example.com", email="a@example.com"):
    return Business(name="Biz", address="Addr", website=f"https://{domain}", phone=None, email=email, place_id=None)


def test_enriched_calls_org_enrichment(monkeypatch, tmp_path):
    called = {"apollo_bulk": 0, "hunter_domain": 0, "job": 0}

    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "<html></html>")
    monkeypatch.setattr("leadgen.generator.extract_emails", lambda html: ["a@example.com"])
    monkeypatch.setattr("leadgen.generator.apply_email_patterns", lambda b: None)
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: DummyAnalysis())
    monkeypatch.setattr("leadgen.generator.export_jsonl", lambda leads, output: None)
    monkeypatch.setattr("leadgen.generator.export_csv", lambda leads, output: None)

    def fake_bulk(domains):
        called["apollo_bulk"] += 1
        return {"example.com": {"name": "Example Org", "domain": "example.com", "industry": "Tech", "employee_count": 10, "id": "org123"}}

    def fake_hunter(domain, *args, **kwargs):
        called["hunter_domain"] += 1
        return {"data": {"emails": [{"value": "info@example.com", "confidence": 80}]}}

    def fake_job(org_id, client=None):
        called["job"] += 1
        return {"count": 2, "is_hiring": True}

    monkeypatch.setattr("leadgen.generator.apollo_bulk_org_enrich", fake_bulk)
    monkeypatch.setattr("leadgen.generator.hunter_domain_search", fake_hunter)
    monkeypatch.setattr("leadgen.generator.apollo_get_org_job_postings", fake_job)
    # Provide dummy clients so enriched path runs
    class DummyApollo:
        pass
    class DummyHunter:
        api_key = "key"
    monkeypatch.setattr("leadgen.integrations.apollo_client.ApolloClient", lambda *a, **k: DummyApollo(), raising=False)
    monkeypatch.setattr("leadgen.integrations.hunter_client.HunterClient", lambda *a, **k: DummyHunter(), raising=False)

    summary = generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid-enrich",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        businesses=[_lead()],
        status="OK",
        enrichment_tier="enriched",
    )
    assert summary["lead_count"] == 1
    assert called["apollo_bulk"] == 1
    assert called["hunter_domain"] == 1
    assert called["job"] == 1


def test_basic_tier_skips_org_enrichment(monkeypatch, tmp_path):
    def fail(*a, **k):
        raise AssertionError("org enrichment should not be called for basic tier")

    monkeypatch.setattr("leadgen.generator.apollo_bulk_org_enrich", fail)
    monkeypatch.setattr("leadgen.generator.hunter_domain_search", fail)
    monkeypatch.setattr("leadgen.generator.apollo_get_org_job_postings", fail)
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "<html></html>")
    monkeypatch.setattr("leadgen.generator.extract_emails", lambda html: ["a@example.com"])
    monkeypatch.setattr("leadgen.generator.apply_email_patterns", lambda b: None)
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: DummyAnalysis())
    monkeypatch.setattr("leadgen.generator.export_jsonl", lambda leads, output: None)
    monkeypatch.setattr("leadgen.generator.export_csv", lambda leads, output: None)

    summary = generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid-basic",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        businesses=[_lead()],
        status="OK",
        enrichment_tier="basic",
    )
    assert summary["lead_count"] == 1
