"""End-to-end mocked pipeline test.

Full city_sweep flow: collect → dedupe → verify → assemble.
All external dependencies (Supabase, Google Places, Hunter, Apollo) mocked.
"""

import pytest

from leadgen.models import Business, WebsiteAnalysis
from pipeline.collector import collect_candidates
from pipeline.deduper import dedupe_candidates
from pipeline.pack_assembler import assemble_pack
from pipeline.verifier import verify_candidates


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeHunter:
    def verify_email(self, email):
        return {"result": "deliverable", "score": 90, "status": "valid"}

    def domain_search(self, domain):
        return None


class FakeApollo:
    def enrich_person_by_email(self, email):
        return None

    def enrich_company_by_domain(self, domain):
        return {
            "organization": {
                "name": "Test Corp",
                "industry": "Healthcare",
                "employee_count": 25,
            }
        }


def _make_businesses(count=10):
    return [
        Business(
            name=f"Miami Dental {i}",
            address=f"{100 + i} Ocean Dr, Miami, FL 33101, USA",
            website=f"https://miamidental{i}.com",
            phone=f"305-555-{i:04d}",
            email=f"info@miamidental{i}.com",
            email_source="html",
            place_id=f"gp_{i}",
        )
        for i in range(count)
    ]


def _setup_collection_mocks(monkeypatch, count=10):
    businesses = _make_businesses(count)

    monkeypatch.setattr(
        "pipeline.collector.search_places",
        lambda query, limit, include_status: (businesses[:limit], "OK"),
    )
    monkeypatch.setattr(
        "pipeline.collector.get_details",
        lambda biz: biz,
    )
    monkeypatch.setattr(
        "pipeline.collector.fetch_html",
        lambda url: "<html><head><meta name='viewport'></head><body>2025 Test</body></html>",
    )
    monkeypatch.setattr(
        "pipeline.collector.extract_emails",
        lambda html: [],
    )


# ---------------------------------------------------------------------------
# E2E Tests
# ---------------------------------------------------------------------------

class TestPipelineE2E:
    def test_full_city_sweep(self, monkeypatch):
        """Full pipeline: collect 10 → dedupe → verify → assemble."""
        _setup_collection_mocks(monkeypatch, count=10)

        # Stage 1: Collect
        candidates, api_status = collect_candidates(
            query="dentists in Miami FL",
            limit=10,
            batch_id="e2e-batch-1",
        )
        assert api_status == "OK"
        assert len(candidates) == 10
        assert all(c["status"] == "new" for c in candidates)

        # Stage 2: Dedupe
        kept, dupes = dedupe_candidates(candidates)
        assert len(kept) == 10
        assert len(dupes) == 0
        assert all(c["status"] == "deduped" for c in kept)
        assert all("dedup_key" in c for c in kept)

        # Stage 3: Verify
        verified = verify_candidates(
            kept,
            hunter_client=FakeHunter(),
            apollo_client=FakeApollo(),
            batch_id="e2e-batch-1",
        )
        assert len(verified) == 10
        assert all(v["email_verified"] is True for v in verified)
        assert all(v["email_confidence"] > 0 for v in verified)
        assert all(v["lead_quality_score"] > 0 for v in verified)
        assert all(v["verification_batch_id"] == "e2e-batch-1" for v in verified)

        # Stage 4: Assemble
        pack = assemble_pack(
            leads=verified,
            niche="dentists",
            city="Miami",
            state="FL",
            target_count=10,
        )
        assert pack["lead_count"] == 10
        assert pack["email_coverage"] == 1.0
        assert pack["phone_coverage"] == 1.0
        assert pack["avg_lead_quality_score"] > 0
        assert "pack_id" in pack

    def test_zero_google_places_results(self, monkeypatch):
        """Edge case: no results from Google Places."""
        monkeypatch.setattr(
            "pipeline.collector.search_places",
            lambda query, limit, include_status: ([], "ZERO_RESULTS"),
        )

        candidates, api_status = collect_candidates(
            query="nonexistent business",
            limit=10,
        )
        assert candidates == []
        assert api_status == "ZERO_RESULTS"

        # Rest of pipeline handles empty gracefully
        kept, dupes = dedupe_candidates(candidates)
        assert kept == []
        assert dupes == []

        verified = verify_candidates(kept)
        assert verified == []

        pack = assemble_pack(
            leads=verified,
            niche="test",
            city="Nowhere",
        )
        assert pack["lead_count"] == 0
        assert pack["sellable"] is False

    def test_duplicates_removed(self, monkeypatch):
        """Verify duplicates are properly detected and excluded."""
        _setup_collection_mocks(monkeypatch, count=6)

        candidates, _ = collect_candidates("dentists Miami", limit=6, batch_id="dup-test")

        # Manually create duplicates by duplicating phone numbers
        candidates[1]["phone_raw"] = candidates[0]["phone_raw"]
        candidates[1]["name"] = candidates[0]["name"]
        candidates[1]["name_normalized"] = candidates[0]["name_normalized"]

        kept, dupes = dedupe_candidates(candidates)
        assert len(dupes) >= 1
        assert all(d["status"] == "duplicate" for d in dupes)
        assert all(k["status"] == "deduped" for k in kept)
        assert len(kept) + len(dupes) == 6

    def test_pipeline_stats_accurate(self, monkeypatch):
        """Metrics at each stage should be consistent."""
        _setup_collection_mocks(monkeypatch, count=5)

        candidates, _ = collect_candidates("test", limit=5, batch_id="stats-test")
        assert len(candidates) == 5

        kept, dupes = dedupe_candidates(candidates)
        assert len(kept) + len(dupes) == 5

        verified = verify_candidates(
            kept,
            hunter_client=FakeHunter(),
            apollo_client=FakeApollo(),
            batch_id="stats-test",
        )
        assert len(verified) == len(kept)

        pack = assemble_pack(
            leads=verified,
            niche="test",
            city="Miami",
        )
        assert pack["lead_count"] == len(verified)

    def test_enrichment_data_flows_through(self, monkeypatch):
        """Verify that enrichment data from Hunter/Apollo reaches verified leads."""
        _setup_collection_mocks(monkeypatch, count=2)

        candidates, _ = collect_candidates("test", limit=2, batch_id="enrich-test")
        kept, _ = dedupe_candidates(candidates)

        verified = verify_candidates(
            kept,
            hunter_client=FakeHunter(),
            apollo_client=FakeApollo(),
            batch_id="enrich-test",
        )

        for lead in verified:
            assert "hunter" in lead["verification_sources"]
            assert "apollo" in lead["verification_sources"]
            assert lead["provenance"].get("hunter") is not None
            assert lead["provenance"].get("apollo") is not None
