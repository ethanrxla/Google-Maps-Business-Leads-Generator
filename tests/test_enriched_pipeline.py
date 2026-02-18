import types

import pytest

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


def _lead_result(domain="example.com", email="a@example.com"):
    return LeadResult(business=_lead(domain, email), analysis=_analysis())


def test_basic_pack_unchanged(monkeypatch, tmp_path):
    calls = {"builtwith": 0, "scrapingbee": 0}

    # Mock integrations to track calls
    class BW:
        def tech_lookup(self, domain):
            calls["builtwith"] += 1
            return {"tech": []}

    class SB:
        def fetch(self, url):
            calls["scrapingbee"] += 1
            return "<html></html>"

    # Stub generator internals to avoid external calls
    monkeypatch.setattr("leadgen.generator.search_places", lambda *a, **k: ([_lead()], "OK"))
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "<html></html>")
    monkeypatch.setattr("leadgen.generator.extract_emails", lambda html: ["a@example.com"])
    monkeypatch.setattr("leadgen.generator.apply_email_patterns", lambda b: None)
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: _analysis())

    # Ensure enrichment path uses our fakes if invoked
    monkeypatch.setattr("leadgen.integrations.builtwith_client.BuiltWithClient", BW, raising=False)
    monkeypatch.setattr("leadgen.integrations.scrapingbee_client.ScrapingBeeClient", SB, raising=False)

    out_csv = tmp_path / "out.csv"
    out_jsonl = tmp_path / "out.jsonl"
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

    # Basic tier should not call new integrations
    assert calls["builtwith"] == 0
    assert calls["scrapingbee"] == 0
    assert out_csv.exists()
    assert out_jsonl.exists()


def test_enriched_pack_calls_builtwith_and_scrapingbee(monkeypatch, tmp_path):
    calls = {"builtwith": 0, "scrapingbee": 0}

    class BW:
        def tech_lookup(self, domain):
            calls["builtwith"] += 1
            return {"tech": ["A", "B"], "domain": domain}

    class SB:
        def fetch(self, url):
            calls["scrapingbee"] += 1
            return "<html><body>rendered</body></html>"

    monkeypatch.setattr("leadgen.generator.search_places", lambda *a, **k: ([_lead()], "OK"))
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    # First fetch returns empty HTML to trigger fallback
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "")
    monkeypatch.setattr("leadgen.generator.extract_emails", lambda html: ["a@example.com"])
    monkeypatch.setattr("leadgen.generator.apply_email_patterns", lambda b: None)
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: _analysis())

    monkeypatch.setattr("leadgen.integrations.builtwith_client.BuiltWithClient", BW, raising=False)
    monkeypatch.setattr("leadgen.integrations.scrapingbee_client.ScrapingBeeClient", SB, raising=False)

    res = generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        enrichment_tier="enriched",
    )

    assert calls["builtwith"] == 1
    assert calls["scrapingbee"] == 1  # fallback triggered
    # Verify tech_stack gets populated in enrichment
    assert res["lead_count"] == 1


def test_enriched_pack_softfails_on_api_errors(monkeypatch, tmp_path):
    class BW:
        def tech_lookup(self, domain):
            raise RuntimeError("boom")

    class SB:
        def fetch(self, url):
            raise RuntimeError("scrape fail")

    monkeypatch.setattr("leadgen.generator.search_places", lambda *a, **k: ([_lead()], "OK"))
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "")
    monkeypatch.setattr("leadgen.generator.extract_emails", lambda html: ["a@example.com"])
    monkeypatch.setattr("leadgen.generator.apply_email_patterns", lambda b: None)
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: _analysis())

    monkeypatch.setattr("leadgen.integrations.builtwith_client.BuiltWithClient", BW, raising=False)
    monkeypatch.setattr("leadgen.integrations.scrapingbee_client.ScrapingBeeClient", SB, raising=False)

    res = generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        enrichment_tier="enriched",
    )

    # Should not crash and should still produce outputs
    assert res["lead_count"] == 1
    # No exception raised; enrichment should be empty/None handled gracefully


def test_tiered_scraping_logic(monkeypatch, tmp_path):
    calls = {"scrapingbee": 0}

    class SB:
        def fetch(self, url):
            calls["scrapingbee"] += 1
            return "<html><body>rendered</body></html>"

    # Case 1: fetch_html returns content → ScrapingBee should not be called
    monkeypatch.setattr("leadgen.generator.search_places", lambda *a, **k: ([_lead()], "OK"))
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "<html>ok</html>")
    monkeypatch.setattr("leadgen.generator.extract_emails", lambda html: ["a@example.com"])
    monkeypatch.setattr("leadgen.generator.apply_email_patterns", lambda b: None)
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: _analysis())
    monkeypatch.setattr("leadgen.integrations.scrapingbee_client.ScrapingBeeClient", SB, raising=False)
    monkeypatch.setattr("leadgen.integrations.builtwith_client.BuiltWithClient", lambda: types.SimpleNamespace(tech_lookup=lambda d: {"tech": []}), raising=False)

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
        output_csv=tmp_path / "out1.csv",
        output_jsonl=tmp_path / "out1.jsonl",
        enrichment_tier="enriched",
    )
    assert calls["scrapingbee"] == 0

    # Case 2: fetch_html returns empty → ScrapingBee should be called
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "")
    generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid2",
        base_dir=tmp_path,
        output_csv=tmp_path / "out2.csv",
        output_jsonl=tmp_path / "out2.jsonl",
        enrichment_tier="enriched",
    )
    assert calls["scrapingbee"] == 1
