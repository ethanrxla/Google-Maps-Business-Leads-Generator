"""Tests for pipeline/email_validator.py -- shared email validation.

Extracted from quality_gates.py so both quality gates and extract_emails()
can import from a single source of truth.
"""

import pytest

from pipeline.email_validator import compute_email_confidence, is_invalid_email


class TestIsInvalidEmail:
    """Canonical invalid-email detection used across the pipeline."""

    # --- Known-bad patterns from real data ---

    @pytest.mark.parametrize("bad_email", [
        "fancybox_sprite@2x.png",
        "logo@company.jpg",
        "icon@site.svg",
        "banner@site.webp",
        "photo@gallery.gif",
        "thumb@images.ico",
        "bg@theme.bmp",
        "avatar@user.jpeg",
    ])
    def test_image_file_extensions_rejected(self, bad_email):
        assert is_invalid_email(bad_email) is True

    @pytest.mark.parametrize("bad_email", [
        "abc123@o456.ingest.sentry.io",
        "dsn@sentry.io",
        "something@wixpress.com",
        "cdn@cloudflare.com",
        "user@example.com",
        "noreply@company.com",
        "test@anything.com",
    ])
    def test_known_bad_tokens_rejected(self, bad_email):
        assert is_invalid_email(bad_email) is True

    # --- Valid emails that must NOT be rejected ---

    @pytest.mark.parametrize("good_email", [
        "info@dentistmiami.com",
        "contact@mybiz.org",
        "hello@startup.io",
        "admin@company.net",
        "sales@shop.co",
        "dr.smith@dental.com",
    ])
    def test_valid_emails_accepted(self, good_email):
        assert is_invalid_email(good_email) is False

    # --- Edge cases ---

    def test_empty_string(self):
        assert is_invalid_email("") is True

    def test_none(self):
        assert is_invalid_email(None) is True

    def test_whitespace_only(self):
        assert is_invalid_email("   ") is True

    def test_no_at_sign(self):
        assert is_invalid_email("notanemail") is True

    def test_integer_input(self):
        assert is_invalid_email(42) is True


class TestComputeEmailConfidence:
    """Tests for the multi-signal email confidence scorer."""

    def test_no_signals(self):
        assert compute_email_confidence() == 0

    def test_hunter_deliverable(self):
        assert compute_email_confidence(hunter_result="deliverable") == 40

    def test_hunter_risky(self):
        assert compute_email_confidence(hunter_result="risky") == 15

    def test_hunter_undeliverable(self):
        assert compute_email_confidence(hunter_result="undeliverable") == 0

    def test_hunter_score_scaling(self):
        assert compute_email_confidence(hunter_score=100) == 30
        assert compute_email_confidence(hunter_score=50) == 15
        assert compute_email_confidence(hunter_score=0) == 0

    def test_apollo_confidence_scaling(self):
        assert compute_email_confidence(apollo_confidence=100) == 20
        assert compute_email_confidence(apollo_confidence=50) == 10

    def test_source_bonus(self):
        assert compute_email_confidence(source="hunter_verified") == 10
        assert compute_email_confidence(source="html") == 0

    def test_combined_maximum(self):
        score = compute_email_confidence(
            hunter_result="deliverable",
            hunter_score=100,
            apollo_confidence=100,
            source="hunter_verified",
        )
        assert score == 100

    def test_combined_partial(self):
        score = compute_email_confidence(
            hunter_result="deliverable",
            hunter_score=80,
        )
        # 40 + 24 = 64
        assert score == 64

    def test_capped_at_100(self):
        score = compute_email_confidence(
            hunter_result="deliverable",
            hunter_score=100,
            apollo_confidence=100,
            source="apollo_verified",
        )
        assert score == 100
