import csv
import json
from pathlib import Path

from leadgen.generator import generate_pack
from leadgen.models import Business, WebsiteAnalysis, LeadResult


def _analysis():
    return WebsiteAnalysis(
        has_website=True,
        needs_website=False,
        needs_redesign=False,
        needs_chatbot=False,
        needs_ai_integration=False,
        raw_data={},
    )


def _lead(domain="example.com", email="a@example.com"):
    return Business(name="Biz", address="Addr", website=f"https://{domain}", phone=None, email=email, place_id=None)


def test_basic_pack_export_unchanged(monkeypatch, tmp_path):
    # Stub pipeline to avoid network calls
    monkeypatch.setattr("leadgen.generator.search_places", lambda *a, **k: ([_lead()], "OK"))
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "<html></html>")
    monkeypatch.setattr("leadgen.generator.extract_emails", lambda html: ["a@example.com"])
    monkeypatch.setattr("leadgen.generator.apply_email_patterns", lambda b: None)
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: _analysis())

    out_csv = tmp_path / "basic.csv"
    out_jsonl = tmp_path / "basic.jsonl"
    generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid",
        base_dir=tmp_path,
        output_csv=out_csv,
        output_jsonl=out_jsonl,
        enrichment_tier="basic",
    )

    # CSV schema must be unchanged
    with out_csv.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    headers = rows[0]
    assert headers == [
        "name",
        "address",
        "website",
        "phone",
        "email",
        "needs_website",
        "needs_redesign",
        "needs_chatbot",
        "needs_ai_integration",
        "score",
        "recommended_services",
        "outreach_message",
        "enriched_title",
        "verified_email_status",
        "apollo_company",
    ]
    assert len(headers) == 15

    # JSONL should not contain enriched-only fields unless already in enrichment
    lines = out_jsonl.read_text().strip().splitlines()
    obj = json.loads(lines[0])
    assert "tech_stack" not in obj
    assert "scrape_source" not in obj
    assert obj.get("enrichment") is None or "tech_stack" not in obj.get("enrichment", {})


def test_enriched_pack_exports_enriched_columns(monkeypatch, tmp_path):
    calls = {"builtwith": 0, "scrapingbee": 0}

    class BW:
        def tech_lookup(self, domain):
            calls["builtwith"] += 1
            return {"domain": domain, "tech": ["A", "B"]}

    class SB:
        def fetch(self, url):
            calls["scrapingbee"] += 1
            return "<html><body>rendered</body></html>"

    monkeypatch.setattr("leadgen.generator.search_places", lambda *a, **k: ([_lead()], "OK"))
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "")
    monkeypatch.setattr("leadgen.generator.extract_emails", lambda html: ["a@example.com"])
    monkeypatch.setattr("leadgen.generator.apply_email_patterns", lambda b: None)
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: _analysis())
    monkeypatch.setattr("leadgen.integrations.builtwith_client.BuiltWithClient", BW, raising=False)
    monkeypatch.setattr("leadgen.integrations.scrapingbee_client.ScrapingBeeClient", SB, raising=False)
    monkeypatch.setattr("leadgen.generator.hunter_domain_search", lambda *a, **k: {})
    monkeypatch.setattr("leadgen.generator.apollo_bulk_org_enrich", lambda *a, **k: {})
    monkeypatch.setattr("leadgen.generator.apollo_get_org_job_postings", lambda *a, **k: {})

    out_csv = tmp_path / "enriched.csv"
    out_jsonl = tmp_path / "enriched.jsonl"
    generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid",
        base_dir=tmp_path,
        output_csv=out_csv,
        output_jsonl=out_jsonl,
        enrichment_tier="enriched",
    )

    with out_csv.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    headers = rows[0]
    assert headers[: len(EXPECTED_HEADERS)] == EXPECTED_HEADERS
    # New enriched-only columns should be appended (imported from export module)
    from leadgen.export import ENRICHED_EXTRA_HEADERS
    assert headers[-len(ENRICHED_EXTRA_HEADERS) :] == ENRICHED_EXTRA_HEADERS

    # JSONL should include tech_stack and scrape_source
    obj = json.loads(out_jsonl.read_text().strip().splitlines()[0])
    assert "tech_stack" in obj.get("enrichment", {}) or obj.get("tech_stack") is not None
    assert obj.get("scrape_source") in ("scrapingbee_fallback", "basic_html")


def test_enriched_export_softfails_empty_enrichment(monkeypatch, tmp_path):
    class BW:
        def tech_lookup(self, domain):
            return None

    class SB:
        def fetch(self, url):
            return None

    monkeypatch.setattr("leadgen.generator.search_places", lambda *a, **k: ([_lead()], "OK"))
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "")
    monkeypatch.setattr("leadgen.generator.extract_emails", lambda html: ["a@example.com"])
    monkeypatch.setattr("leadgen.generator.apply_email_patterns", lambda b: None)
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: _analysis())
    monkeypatch.setattr("leadgen.integrations.builtwith_client.BuiltWithClient", BW, raising=False)
    monkeypatch.setattr("leadgen.integrations.scrapingbee_client.ScrapingBeeClient", SB, raising=False)
    monkeypatch.setattr("leadgen.generator.hunter_domain_search", lambda *a, **k: {})
    monkeypatch.setattr("leadgen.generator.apollo_bulk_org_enrich", lambda *a, **k: {})
    monkeypatch.setattr("leadgen.generator.apollo_get_org_job_postings", lambda *a, **k: {})

    out_csv = tmp_path / "soft.csv"
    out_jsonl = tmp_path / "soft.jsonl"
    generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid",
        base_dir=tmp_path,
        output_csv=out_csv,
        output_jsonl=out_jsonl,
        enrichment_tier="enriched",
    )

    with out_csv.open(newline="", encoding="utf-8") as f:
        headers = list(csv.reader(f))[0]
    from leadgen.export import ENRICHED_EXTRA_HEADERS
    assert headers[-len(ENRICHED_EXTRA_HEADERS) :] == ENRICHED_EXTRA_HEADERS

    obj = json.loads(out_jsonl.read_text().strip().splitlines()[0])
    # Fields should exist but may be None/empty
    assert "tech_stack" in obj.get("enrichment", {}) or obj.get("tech_stack") is None
    assert "scrape_source" in obj
from tests.test_export import EXPECTED_HEADERS
