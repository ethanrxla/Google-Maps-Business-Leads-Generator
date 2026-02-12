"""Tests for pipeline/models.py -- source/status validation and to_dict.

Covers the deterministic source_method policy: every Candidate
must have a source from VALID_SOURCES, every status from VALID_STATUSES.
"""

import pytest
from datetime import datetime, timezone

from pipeline.models import (
    Candidate,
    VerifiedLead,
    VALID_SOURCES,
    VALID_STATUSES,
    validate_source,
    validate_status,
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

    def test_invalid_source_on_creation(self):
        with pytest.raises(ValueError, match="Invalid source"):
            Candidate(name="Bad", name_normalized="bad", source="twitter")

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
