"""Tests for pipeline/models.py -- source/status validation and to_dict.

Covers the deterministic source_method policy: every Candidate
must have a source from VALID_SOURCES, every status from VALID_STATUSES.
"""

import pytest
from datetime import datetime, timezone

from pipeline.models import (
    Candidate,
    Pack,
    VerifiedLead,
    VALID_ENRICHMENT_TIERS,
    VALID_SOURCES,
    VALID_STATUSES,
    validate_enrichment_tier,
    validate_source,
    validate_status,
    normalize_source,
)


# ---------------------------------------------------------------------------
# Source validation
# ---------------------------------------------------------------------------

class TestValidateSource:
    @pytest.mark.parametrize("source", sorted(VALID_SOURCES))
    def test_all_valid_sources_accepted(self, source):
        assert validate_source(source) == source

    @pytest.mark.parametrize("bad", [
        "twitter_scrape", "linkedin", "GOOGLE_PLACES",
        "google", "scrape", "", "  ",
    ])
    def test_invalid_sources_rejected(self, bad):
        with pytest.raises(ValueError, match="Invalid source"):
            validate_source(bad)

    def test_enum_matches_db_constraint(self):
        """VALID_SOURCES must match the CHECK constraint in 001_core_tables.sql."""
        expected = {"google_places", "theharvester", "manual", "serp", "html_scrape"}
        assert VALID_SOURCES == expected


class TestNormalizeSource:
    """normalize_source() maps legacy values to canonical VALID_SOURCES."""

    @pytest.mark.parametrize("source", sorted(VALID_SOURCES))
    def test_canonical_values_unchanged(self, source):
        assert normalize_source(source) == source

    @pytest.mark.parametrize("legacy,expected", [
        ("google", "google_places"),
        ("maps", "google_places"),
        ("places", "google_places"),
        ("google_maps", "google_places"),
        ("twitter", "serp"),
        ("twitter search", "serp"),
        ("x search", "serp"),
        ("search", "serp"),
        ("harvester", "theharvester"),
        ("the_harvester", "theharvester"),
        ("html", "html_scrape"),
        ("scrape", "html_scrape"),
        ("crawl", "html_scrape"),
        ("web_scrape", "html_scrape"),
    ])
    def test_legacy_values_mapped(self, legacy, expected):
        assert normalize_source(legacy) == expected

    def test_blank_defaults_to_manual(self):
        assert normalize_source("") == "manual"

    def test_whitespace_defaults_to_manual(self):
        assert normalize_source("   ") == "manual"

    def test_unmappable_returns_as_is(self):
        """Truly unknown values pass through for validate_source() to catch."""
        assert normalize_source("totally_unknown_xyz") == "totally_unknown_xyz"

    def test_case_insensitive(self):
        assert normalize_source("GOOGLE") == "google_places"
        assert normalize_source("Twitter") == "serp"


class TestValidateStatus:
    @pytest.mark.parametrize("status", sorted(VALID_STATUSES))
    def test_all_valid_statuses_accepted(self, status):
        assert validate_status(status) == status

    @pytest.mark.parametrize("bad", [
        "qualified", "verified", "ready", "contacted",
        "active", "", "NEW",
    ])
    def test_invalid_statuses_rejected(self, bad):
        with pytest.raises(ValueError, match="Invalid status"):
            validate_status(bad)


# ---------------------------------------------------------------------------
# Candidate dataclass
# ---------------------------------------------------------------------------

class TestCandidate:
    def test_valid_creation(self):
        c = Candidate(
            name="Test Biz",
            name_normalized="test-biz",
            source="google_places",
        )
        assert c.source == "google_places"
        assert c.status == "new"

    def test_legacy_source_normalized_on_creation(self):
        """Legacy sources get normalized instead of crashing."""
        c = Candidate(name="Biz", name_normalized="biz", source="twitter")
        assert c.source == "serp"

    def test_truly_invalid_source_on_creation(self):
        with pytest.raises(ValueError, match="Invalid source"):
            Candidate(name="Bad", name_normalized="bad", source="totally_unknown_xyz")

    def test_invalid_status_on_creation(self):
        with pytest.raises(ValueError, match="Invalid status"):
            Candidate(
                name="Bad", name_normalized="bad",
                source="manual", status="verified",
            )

    def test_to_dict_drops_none_and_id(self):
        c = Candidate(
            name="Test",
            name_normalized="test",
            source="manual",
            city="Miami",
        )
        d = c.to_dict()
        assert "id" not in d
        assert d["name"] == "Test"
        assert d["city"] == "Miami"
        assert "lat" not in d  # None values dropped
        assert "lng" not in d

    def test_to_dict_serializes_datetime(self):
        dt = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        c = Candidate(
            name="Test",
            name_normalized="test",
            source="manual",
            collected_at=dt,
        )
        d = c.to_dict()
        assert d["collected_at"] == "2026-02-01T12:00:00+00:00"

    @pytest.mark.parametrize("source", sorted(VALID_SOURCES))
    def test_all_sources_constructable(self, source):
        c = Candidate(name="X", name_normalized="x", source=source)
        assert c.source == source

    def test_defaults(self):
        c = Candidate(name="X", name_normalized="x", source="manual")
        assert c.country == "US"
        assert c.status == "new"
        assert c.id is None
        assert c.email_raw is None


# ---------------------------------------------------------------------------
# VerifiedLead dataclass
# ---------------------------------------------------------------------------

class TestVerifiedLead:
    def test_valid_creation(self):
        v = VerifiedLead(
            name="Verified Biz",
            name_normalized="verified-biz",
            candidate_ids=["uuid-1"],
        )
        assert v.email_confidence == 0
        assert v.needs_score == 0
        assert v.verification_sources == []

    def test_to_dict_drops_none_and_id(self):
        v = VerifiedLead(
            name="Test",
            name_normalized="test",
            candidate_ids=["a"],
            email="info@test.com",
        )
        d = v.to_dict()
        assert "id" not in d
        assert d["email"] == "info@test.com"
        assert d["candidate_ids"] == ["a"]
        assert "linkedin_url" not in d  # None dropped

    def test_defaults(self):
        v = VerifiedLead(name="X", name_normalized="x")
        assert v.country == "US"
        assert v.phone_verified is False
        assert v.email_verified is False
        assert v.has_website is False
        assert v.provenance == {}
        assert v.recommended_services == []


# ---------------------------------------------------------------------------
# Pack dataclass
# ---------------------------------------------------------------------------

class TestPack:
    def test_valid_creation(self):
        p = Pack(pack_id="us_fl_miami_dentists_50", niche="dentists", city="Miami")
        assert p.pack_id == "us_fl_miami_dentists_50"
        assert p.enrichment_tier == "basic"
        assert p.sellable is False
        assert p.lead_count == 0
        assert p.assembled_at is not None
        assert p.expires_at is not None
        assert p.expires_at > p.assembled_at

    def test_enriched_tier(self):
        p = Pack(pack_id="p1", niche="n", city="c", enrichment_tier="enriched")
        assert p.enrichment_tier == "enriched"

    def test_invalid_enrichment_tier(self):
        with pytest.raises(ValueError, match="Invalid enrichment_tier"):
            Pack(pack_id="p1", niche="n", city="c", enrichment_tier="premium")

    def test_valid_enrichment_tiers_set(self):
        assert VALID_ENRICHMENT_TIERS == {"basic", "enriched"}

    def test_to_dict_drops_none_and_id(self):
        p = Pack(
            pack_id="p1", niche="dentists", city="Miami",
            lead_count=25, sellable=True,
        )
        d = p.to_dict()
        assert "id" not in d
        assert d["pack_id"] == "p1"
        assert d["lead_count"] == 25
        assert d["sellable"] is True
        assert "state" not in d  # None dropped

    def test_to_dict_serializes_datetimes(self):
        dt = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        p = Pack(
            pack_id="p1", niche="n", city="c",
            assembled_at=dt,
        )
        d = p.to_dict()
        assert d["assembled_at"] == "2026-02-01T12:00:00+00:00"

    def test_defaults(self):
        p = Pack(pack_id="p1", niche="n", city="c")
        assert p.country == "US"
        assert p.email_coverage == 0.0
        assert p.phone_coverage == 0.0
        assert p.avg_lead_quality_score == 0.0
        assert p.quality_gate_failures == []
        assert p.csv_path is None

    def test_custom_expiry(self):
        dt = datetime(2026, 6, 1)
        exp = datetime(2026, 12, 1)
        p = Pack(pack_id="p1", niche="n", city="c", assembled_at=dt, expires_at=exp)
        assert p.expires_at == exp

    def test_validate_enrichment_tier_function(self):
        assert validate_enrichment_tier("basic") == "basic"
        assert validate_enrichment_tier("enriched") == "enriched"
        with pytest.raises(ValueError):
            validate_enrichment_tier("gold")
