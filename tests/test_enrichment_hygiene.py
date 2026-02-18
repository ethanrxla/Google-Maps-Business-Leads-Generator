"""Tests for enrichment error hygiene.

Ensures API error responses are never stored as valid enrichment data.
Covers: _safe_call error dicts, BuiltWith API errors, tech_stack sanitization.
"""

import pytest

from leadgen.enrichment import is_enrichment_error


class TestIsEnrichmentError:
    """Detect API error responses masquerading as valid data."""

    def test_safe_call_error_dict_detected(self):
        assert is_enrichment_error({"error": "Connection timed out"}) is True

    def test_safe_call_error_empty_string(self):
        assert is_enrichment_error({"error": ""}) is True

    def test_builtwith_errors_key_detected(self):
        payload = {"Errors": [{"Message": "API Credits: 0"}]}
        assert is_enrichment_error(payload) is True

    def test_builtwith_errors_empty_list(self):
        """Even empty Errors list means the response is error-shaped."""
        payload = {"Errors": []}
        assert is_enrichment_error(payload) is True

    def test_builtwith_credits_zero_text(self):
        payload = {"message": "API Credits: 0", "status": "error"}
        assert is_enrichment_error(payload) is True

    def test_valid_tech_stack_not_flagged(self):
        payload = {
            "Results": [{"Technologies": [{"Name": "WordPress"}]}],
        }
        assert is_enrichment_error(payload) is False

    def test_valid_hunter_data_not_flagged(self):
        payload = {
            "data": {"emails": [{"value": "info@dentist.com", "confidence": 90}]},
        }
        assert is_enrichment_error(payload) is False

    def test_valid_apollo_data_not_flagged(self):
        payload = {"organization": {"name": "Test Corp", "industry": "Health"}}
        assert is_enrichment_error(payload) is False

    def test_none_is_error(self):
        assert is_enrichment_error(None) is True

    def test_empty_dict_is_error(self):
        assert is_enrichment_error({}) is True

    def test_non_dict_is_error(self):
        assert is_enrichment_error("some string") is True
        assert is_enrichment_error(42) is True
        assert is_enrichment_error([]) is True

    def test_rate_limited_response(self):
        payload = {"rate_limited": True, "error": "Rate limit exceeded"}
        assert is_enrichment_error(payload) is True
