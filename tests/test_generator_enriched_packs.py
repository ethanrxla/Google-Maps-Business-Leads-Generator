from leadgen.generator import generate_pack
from leadgen.models import Business, WebsiteAnalysis, LeadResult


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


def test_basic_tier_does_not_call_enrich(monkeypatch, tmp_path):
    called = {}

    monkeypatch.setattr("leadgen.integrations.apollo_client.ApolloClient", None, raising=False)
    monkeypatch.setattr("leadgen.integrations.hunter_client.HunterClient", None, raising=False)
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "")
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: DummyAnalysis())

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
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        businesses=[_lead()],
        status="OK",
        enrichment_tier="basic",
    )


def test_enriched_tier_calls_enrich(monkeypatch, tmp_path):
    calls = {"apollo": 0, "hunter": 0}

    class FakeApollo:
        def __init__(self, *a, **k):
            self.api_key = "key"
            self.BASE_URL = "https://api.apollo.test"

        def enrich_person_by_email(self, email):
            calls["apollo"] += 1
            return {"person": {"email": email, "title": "CEO"}}

        def enrich_company_by_domain(self, domain):
            calls.setdefault("apollo_company", 0)
            calls["apollo_company"] += 1
            return {"organization": {"domain": domain, "name": "Biz Org"}}

    class FakeHunter:
        def __init__(self, *a, **k):
            pass

        def verify_email(self, email):
            calls["hunter"] += 1
            return {"result": "deliverable"}

    monkeypatch.setattr("leadgen.integrations.apollo_client.ApolloClient", FakeApollo, raising=False)
    monkeypatch.setattr("leadgen.integrations.hunter_client.HunterClient", FakeHunter, raising=False)
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "")
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: DummyAnalysis())

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
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        businesses=[_lead()],
        status="OK",
        enrichment_tier="enriched",
    )

    assert calls["apollo"] == 1
    assert calls["hunter"] == 1
    assert calls.get("apollo_company", 0) == 1


def test_enriched_soft_fails_without_keys(monkeypatch, tmp_path):
    # Clients will return missing key errors; should not crash
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "")
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: DummyAnalysis())
    monkeypatch.setattr("leadgen.integrations.apollo_client.ApolloClient", None, raising=False)
    monkeypatch.setattr("leadgen.integrations.hunter_client.HunterClient", None, raising=False)
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
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        businesses=[_lead()],
        status="OK",
        enrichment_tier="enriched",
    )


def test_basic_pack_does_not_call_builtwith_or_scrapingbee(monkeypatch, tmp_path):
    calls = {"bw": 0, "sb": 0}

    class BW:
        def __init__(self, *a, **k):
            calls["bw"] += 1

    class SB:
        def __init__(self, *a, **k):
            calls["sb"] += 1

    monkeypatch.setattr("leadgen.generator.search_places", lambda *a, **k: ([_lead()], "OK"))
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "<html></html>")
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: DummyAnalysis())
    monkeypatch.setattr("leadgen.integrations.builtwith_client.BuiltWithClient", BW, raising=False)
    monkeypatch.setattr("leadgen.integrations.scrapingbee_client.ScrapingBeeClient", SB, raising=False)

    generate_pack(
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
        enrichment_tier="basic",
    )

    assert calls["bw"] == 0
    assert calls["sb"] == 0


def test_enriched_pack_calls_builtwith_for_leads_with_domain(monkeypatch, tmp_path):
    calls = {"bw": 0}

    class BW:
        def __init__(self, *a, **k):
            pass

        def tech_lookup(self, domain):
            calls["bw"] += 1
            return {"domain": domain, "tech": ["A", "B"]}

    monkeypatch.setattr("leadgen.generator.search_places", lambda *a, **k: ([_lead()], "OK"))
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "<html></html>")
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: DummyAnalysis())
    monkeypatch.setattr("leadgen.integrations.builtwith_client.BuiltWithClient", BW, raising=False)

    generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid-enriched",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        enrichment_tier="enriched",
    )

    assert calls["bw"] == 1


def test_enriched_pack_uses_scrapingbee_when_basic_fetch_html_is_empty(monkeypatch, tmp_path):
    calls = {"sb": 0}

    class SB:
        def __init__(self, *a, **k):
            pass

        def fetch(self, url):
            calls["sb"] += 1
            return "<html><body>rendered</body></html>"

    monkeypatch.setattr("leadgen.generator.search_places", lambda *a, **k: ([_lead()], "OK"))
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "")
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: DummyAnalysis())
    monkeypatch.setattr("leadgen.integrations.scrapingbee_client.ScrapingBeeClient", SB, raising=False)

    generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid-sb",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        enrichment_tier="enriched",
    )

    assert calls["sb"] == 1


def test_enriched_pack_soft_fails_when_enrichment_api_errors(monkeypatch, tmp_path):
    class BW:
        def __init__(self, *a, **k):
            pass

        def tech_lookup(self, domain):
            raise RuntimeError("bw fail")

    class SB:
        def __init__(self, *a, **k):
            pass

        def fetch(self, url):
            raise RuntimeError("sb fail")

    monkeypatch.setattr("leadgen.generator.search_places", lambda *a, **k: ([_lead()], "OK"))
    monkeypatch.setattr("leadgen.generator.get_details", lambda b: b)
    monkeypatch.setattr("leadgen.generator.fetch_html", lambda url: "")
    monkeypatch.setattr("leadgen.generator.analyze_html", lambda html: DummyAnalysis())
    monkeypatch.setattr("leadgen.integrations.builtwith_client.BuiltWithClient", BW, raising=False)
    monkeypatch.setattr("leadgen.integrations.scrapingbee_client.ScrapingBeeClient", SB, raising=False)

    result = generate_pack(
        query="q",
        country="usa",
        state="fl",
        county=None,
        city="city",
        niche="niche",
        limit=1,
        pack_id="pid-soft",
        base_dir=tmp_path,
        output_csv=tmp_path / "out.csv",
        output_jsonl=tmp_path / "out.jsonl",
        enrichment_tier="enriched",
    )

    assert result["lead_count"] == 1
