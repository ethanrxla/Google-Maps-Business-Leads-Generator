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


def _lead(domain="example.com", email=None):
    return Business(name="Biz", address="Addr", website=f"https://{domain}", phone=None, email=email, place_id=None)


def test_contact_page_fetch_fills_email(monkeypatch, tmp_path):
    calls = []

    def fake_fetch(url):
        calls.append(url)
        if "contact" in url:
            return "<html>contact@example.com</html>"
        return ""

    def fake_extract_emails(html):
        if "contact@example.com" in html:
            return ["contact@example.com"]
        return []

    captured = {}

    monkeypatch.setattr("leadgen.generator.fetch_html", fake_fetch)
    monkeypatch.setattr("leadgen.generator.extract_emails", fake_extract_emails)
    monkeypatch.setattr("leadgen.generator.apply_email_patterns", lambda b: None)
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: DummyAnalysis())
    monkeypatch.setattr("leadgen.generator.export_jsonl", lambda leads, output: None)

    def fake_export_csv(results, output):
        captured["results"] = results

    monkeypatch.setattr("leadgen.generator.export_csv", fake_export_csv)

    generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid-contact",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        businesses=[_lead()],
        status="OK",
        enrichment_tier="enriched",
    )

    assert any("contact" in url for url in calls)
    lead = captured["results"][0]
    assert lead.business.email == "contact@example.com"
    assert lead.business.email_source == "contact_page"


def test_hunter_domain_search_used_when_no_email(monkeypatch, tmp_path):
    calls = {"domain": 0, "verify": 0}

    class FakeHunter:
        def __init__(self, *a, **k):
            self.api_key = "key"

        def domain_search(self, domain, limit=5):
            calls["domain"] += 1
            return {"data": {"emails": [{"value": "info@example.com", "confidence": 90}]}}

        def verify_email(self, email):
            calls["verify"] += 1
            return {"result": "deliverable", "score": 95}

    monkeypatch.setattr("leadgen.integrations.hunter_client.HunterClient", FakeHunter, raising=False)
    monkeypatch.setattr("leadgen.integrations.apollo_client.ApolloClient", None, raising=False)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "")
    monkeypatch.setattr("leadgen.generator.extract_emails", lambda html: [])
    monkeypatch.setattr("leadgen.generator.apply_email_patterns", lambda b: None)
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: DummyAnalysis())
    monkeypatch.setattr("leadgen.generator.export_jsonl", lambda leads, output: None)

    captured = {}

    def fake_export_csv(results, output):
        captured["results"] = results

    monkeypatch.setattr("leadgen.generator.export_csv", fake_export_csv)

    generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid-hunter",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        businesses=[_lead()],
        status="OK",
        enrichment_tier="enriched",
    )

    assert calls["domain"] == 1
    lead = captured["results"][0]
    assert lead.business.email == "info@example.com"
    assert lead.business.email_source == "hunter_domain_search"
