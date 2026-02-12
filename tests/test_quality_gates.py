"""Tests for pipeline/quality_gates.py -- explicit pass/fail verification.

Snapshot-style: each test documents expected behavior for a specific gate.
"""

import pytest

from pipeline.quality_gates import (
    check_quality_gates,
    is_invalid_email,
    _gate_email_coverage,
    _gate_email_validity,
    _gate_email_verified,
    _gate_phone_coverage,
    _gate_website_coverage,
    _gate_deduplication,
    _gate_pack_fill,
    _gate_freshness_days,
    _gate_score_distribution,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lead(**overrides):
    """Build a lead dict with reasonable defaults that pass all gates."""
    base = {
        "name": "Test Business",
        "name_normalized": "test-business",
        "email": "info@test.com",
        "email_verified": True,
        "phone": "(555) 123-4567",
        "website": "https://test.com",
        "needs_score": 40,
        "lead_quality_score": 60,
        "data_freshness_days": 5,
        "dedup_key": None,  # will be set per test
    }
    base.update(overrides)
    return base


def _make_pack(n=10, **lead_overrides):
    """Build n leads with unique dedup_keys."""
    return [
        _lead(dedup_key=f"key-{i}", name_normalized=f"biz-{i}", **lead_overrides)
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# is_invalid_email
# ---------------------------------------------------------------------------

class TestIsInvalidEmail:
    @pytest.mark.parametrize("email", [
        "fancybox_sprite@2x.png",
        "common-questions@2x.png",
        "flags@2x.webp",
        "icon@sprite.jpg",
    ])
    def test_image_files_rejected(self, email):
        assert is_invalid_email(email) is True

    @pytest.mark.parametrize("email", [
        "605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com",
        "test@example.com",
        "noreply@company.com",
    ])
    def test_known_bad_patterns_rejected(self, email):
        assert is_invalid_email(email) is True

    @pytest.mark.parametrize("email", [
        "info@dentist.com",
        "hello@mycompany.co",
        "contact@restaurant.net",
        "john.smith@company.com",
    ])
    def test_valid_emails_accepted(self, email):
        assert is_invalid_email(email) is False

    @pytest.mark.parametrize("email", [None, "", "   ", "notanemail"])
    def test_empty_and_malformed_rejected(self, email):
        assert is_invalid_email(email) is True


# ---------------------------------------------------------------------------
# Individual gate tests
# ---------------------------------------------------------------------------

class TestGateEmailCoverage:
    def test_passes_at_threshold_basic(self):
        leads = _make_pack(10)  # all have email
        assert _gate_email_coverage(leads, enriched=False) is None

    def test_fails_below_threshold_basic(self):
        leads = _make_pack(10)
        for i in range(4):  # remove 4 emails -> 60% < 70%
            leads[i]["email"] = None
        result = _gate_email_coverage(leads, enriched=False)
        assert result is not None
        assert "60%" in result

    def test_enriched_has_higher_threshold(self):
        leads = _make_pack(10)
        for i in range(2):  # 80% < 85%
            leads[i]["email"] = None
        assert _gate_email_coverage(leads, enriched=True) is not None
        assert _gate_email_coverage(leads, enriched=False) is None  # 80% >= 70%

    def test_empty_leads(self):
        assert _gate_email_coverage([], enriched=False) == "no_leads"


class TestGateEmailValidity:
    def test_passes_all_valid(self):
        leads = _make_pack(5)
        assert _gate_email_validity(leads) is None

    def test_fails_with_image_email(self):
        leads = _make_pack(5)
        leads[0]["email"] = "sprite@2x.png"
        result = _gate_email_validity(leads)
        assert result is not None
        assert "invalid_emails: 1" in result

    def test_catches_sentry_email(self):
        leads = _make_pack(5)
        leads[0]["email"] = "abc123@sentry-next.wixpress.com"
        assert _gate_email_validity(leads) is not None

    def test_none_email_not_flagged(self):
        leads = _make_pack(5)
        leads[0]["email"] = None
        assert _gate_email_validity(leads) is None


class TestGateEmailVerified:
    def test_skipped_for_basic(self):
        leads = _make_pack(5, email_verified=False)
        assert _gate_email_verified(leads, enriched=False) is None

    def test_passes_enriched_at_threshold(self):
        leads = _make_pack(10, email_verified=False)
        for i in range(3):  # 30% verified
            leads[i]["email_verified"] = True
        assert _gate_email_verified(leads, enriched=True) is None

    def test_fails_enriched_below_threshold(self):
        leads = _make_pack(10, email_verified=False)
        leads[0]["email_verified"] = True  # only 10%
        result = _gate_email_verified(leads, enriched=True)
        assert result is not None
        assert "10%" in result


class TestGatePhoneCoverage:
    def test_passes_basic(self):
        leads = _make_pack(10)
        assert _gate_phone_coverage(leads, enriched=False) is None

    def test_fails_basic(self):
        leads = _make_pack(10)
        for i in range(3):
            leads[i]["phone"] = None  # 70% < 75%
        assert _gate_phone_coverage(leads, enriched=False) is not None


class TestGateWebsiteCoverage:
    def test_passes(self):
        leads = _make_pack(10)
        assert _gate_website_coverage(leads) is None

    def test_fails(self):
        leads = _make_pack(10)
        for i in range(5):
            leads[i]["website"] = None  # 50% < 60%
        assert _gate_website_coverage(leads) is not None


class TestGateDeduplication:
    def test_passes_unique_keys(self):
        leads = _make_pack(5)
        assert _gate_deduplication(leads) is None

    def test_fails_with_duplicates(self):
        leads = _make_pack(5)
        leads[0]["dedup_key"] = "same-key"
        leads[1]["dedup_key"] = "same-key"
        result = _gate_deduplication(leads)
        assert result is not None
        assert "duplicates_in_pack: 1" in result

    def test_falls_back_to_name_normalized(self):
        leads = _make_pack(5)
        for l in leads:
            l["dedup_key"] = None
        leads[0]["name_normalized"] = "dupe"
        leads[1]["name_normalized"] = "dupe"
        assert _gate_deduplication(leads) is not None


class TestGatePackFill:
    def test_passes_at_threshold(self):
        leads = _make_pack(8)
        assert _gate_pack_fill(leads, target_count=10) is None  # 80% exact

    def test_fails_below_threshold(self):
        leads = _make_pack(7)
        result = _gate_pack_fill(leads, target_count=10)
        assert result is not None
        assert "underfilled" in result

    def test_zero_target_skips(self):
        assert _gate_pack_fill([], target_count=0) is None


class TestGateFreshness:
    def test_passes_fresh_data(self):
        leads = _make_pack(5, data_freshness_days=30)
        assert _gate_freshness_days(leads) is None

    def test_fails_stale_data(self):
        leads = _make_pack(5)
        leads[0]["data_freshness_days"] = 120
        result = _gate_freshness_days(leads)
        assert result is not None
        assert "stale_leads: 1" in result


class TestGateScoreDistribution:
    def test_passes_good_distribution(self):
        leads = _make_pack(10, needs_score=40)
        assert _gate_score_distribution(leads) is None

    def test_fails_low_average(self):
        leads = _make_pack(10, needs_score=10)
        result = _gate_score_distribution(leads)
        assert result is not None
        assert "avg_needs_score" in result

    def test_fails_low_high_score_pct(self):
        leads = _make_pack(10, needs_score=20)  # avg=20 >= 15, but 0% >= 30
        result = _gate_score_distribution(leads)
        assert result is not None
        assert "high_score_pct" in result


# ---------------------------------------------------------------------------
# Integration: full gate runner
# ---------------------------------------------------------------------------

class TestCheckQualityGates:
    def test_all_pass(self):
        leads = _make_pack(10, needs_score=40)
        passed, failures = check_quality_gates(leads, target_count=10)
        assert passed is True
        assert failures == []

    def test_multiple_failures(self):
        leads = _make_pack(10)
        for i in range(5):
            leads[i]["email"] = None
            leads[i]["phone"] = None
        leads[0]["email"] = "sprite@2x.png"
        passed, failures = check_quality_gates(leads, target_count=10)
        assert passed is False
        assert len(failures) >= 2  # email_coverage + phone_coverage at minimum

    def test_enriched_stricter(self):
        leads = _make_pack(10, email_verified=False, needs_score=40)
        passed_basic, _ = check_quality_gates(leads, enriched=False)
        passed_enriched, failures_enriched = check_quality_gates(leads, enriched=True)
        assert passed_basic is True
        assert passed_enriched is False
        assert any("email_verified" in f for f in failures_enriched)

    def test_empty_pack(self):
        passed, failures = check_quality_gates([])
        assert passed is False
        assert len(failures) > 0

    def test_sellable_snapshot(self):
        """Snapshot: a well-formed basic pack of 20 should pass."""
        leads = _make_pack(20, needs_score=45)
        passed, failures = check_quality_gates(
            leads, target_count=20, enriched=False
        )
        assert passed is True, f"Expected pass but got failures: {failures}"

    def test_unsellable_snapshot(self):
        """Snapshot: pack with bad emails, missing phones, low scores fails."""
        leads = _make_pack(20, needs_score=5)
        for i in range(0, 20, 2):
            leads[i]["email"] = f"img{i}@2x.png"
            leads[i]["phone"] = None
        passed, failures = check_quality_gates(
            leads, target_count=20, enriched=False
        )
        assert passed is False
        assert len(failures) >= 3
