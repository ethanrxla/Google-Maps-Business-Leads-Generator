"""Tests for pipeline/pack_assembler.py -- pack assembly stage."""

import pytest

from pipeline.pack_assembler import assemble_pack


def _make_lead(**overrides):
    """Build a verified lead dict that passes all quality gates."""
    base = {
        "name": "Test Biz",
        "name_normalized": "test_biz",
        "email": "info@test.com",
        "email_verified": True,
        "phone": "555-0001",
        "website": "https://test.com",
        "dedup_key": "test_biz|5550001",
        "needs_score": 40,
        "lead_quality_score": 60,
        "data_freshness_days": 0,
    }
    base.update(overrides)
    return base


def _make_passing_leads(count=10):
    """Create a list of leads that should pass all quality gates."""
    return [
        _make_lead(
            name=f"Biz {i}",
            name_normalized=f"biz_{i}",
            email=f"info{i}@biz{i}.com",
            phone=f"555-{i:04d}",
            website=f"https://biz{i}.com",
            dedup_key=f"biz_{i}|555{i:04d}",
        )
        for i in range(count)
    ]


class TestAssemblePack:
    def test_basic_assembly(self):
        leads = _make_passing_leads(10)
        pack = assemble_pack(
            leads, niche="dentists", city="Miami", state="FL",
        )
        assert pack["niche"] == "dentists"
        assert pack["city"] == "Miami"
        assert pack["lead_count"] == 10
        assert pack["email_coverage"] == 1.0
        assert pack["phone_coverage"] == 1.0
        assert "pack_id" in pack
        assert "assembled_at" in pack
        assert "expires_at" in pack

    def test_sellable_pack(self):
        leads = _make_passing_leads(10)
        pack = assemble_pack(
            leads, niche="dentists", city="Miami",
            target_count=10,
        )
        assert pack["sellable"] is True
        assert pack["quality_gate_failures"] == []

    def test_unsellable_pack_missing_emails(self):
        leads = _make_passing_leads(10)
        for lead in leads[:8]:
            lead["email"] = None
        pack = assemble_pack(
            leads, niche="dentists", city="Miami",
        )
        assert pack["sellable"] is False
        assert len(pack["quality_gate_failures"]) > 0

    def test_empty_leads(self):
        pack = assemble_pack([], niche="dentists", city="Miami")
        assert pack["lead_count"] == 0
        assert pack["sellable"] is False

    def test_metrics_computed(self):
        leads = _make_passing_leads(4)
        leads[0]["lead_quality_score"] = 80
        leads[1]["lead_quality_score"] = 60
        leads[2]["lead_quality_score"] = 40
        leads[3]["lead_quality_score"] = 20
        pack = assemble_pack(leads, niche="dentists", city="Miami")
        assert pack["avg_lead_quality_score"] == 50.0

    def test_pack_id_generated(self):
        leads = _make_passing_leads(5)
        pack = assemble_pack(
            leads, niche="dentists", city="Miami",
            state="FL", country="US",
        )
        assert "miami" in pack["pack_id"].lower() or "dentists" in pack["pack_id"].lower()

    def test_enrichment_tier_passed_through(self):
        leads = _make_passing_leads(5)
        pack = assemble_pack(
            leads, niche="dentists", city="Miami",
            enrichment_tier="enriched",
        )
        assert pack["enrichment_tier"] == "enriched"

    def test_file_paths(self):
        leads = _make_passing_leads(5)
        pack = assemble_pack(
            leads, niche="dentists", city="Miami",
            csv_path="/tmp/pack.csv",
            jsonl_path="/tmp/pack.jsonl",
        )
        assert pack["csv_path"] == "/tmp/pack.csv"
        assert pack["jsonl_path"] == "/tmp/pack.jsonl"

    def test_quality_gate_failures_sorted(self):
        leads = _make_passing_leads(10)
        # Remove most emails to cause email_coverage failure
        for lead in leads[:8]:
            lead["email"] = None
        pack = assemble_pack(leads, niche="dentists", city="Miami")
        # Failures should be sorted strings
        assert pack["quality_gate_failures"] == sorted(pack["quality_gate_failures"])
