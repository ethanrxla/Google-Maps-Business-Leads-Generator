"""Tests for pipeline/verifier.py -- verification + confidence scoring stage."""

import pytest

from pipeline.verifier import verify_candidates


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeHunter:
    def __init__(self, verify_result=None, domain_result=None):
        self._verify_result = verify_result or {
            "result": "deliverable",
            "score": 85,
            "status": "valid",
        }
        self._domain_result = domain_result

    def verify_email(self, email):
        return self._verify_result

    def domain_search(self, domain):
        return self._domain_result


class FakeApollo:
    def __init__(self, person_result=None, company_result=None):
        self._person_result = person_result
        self._company_result = company_result or {
            "organization": {
                "name": "Test Corp",
                "industry": "Technology",
                "employee_count": 50,
            }
        }

    def enrich_person_by_email(self, email):
        return self._person_result

    def enrich_company_by_domain(self, domain):
        return self._company_result


def _make_candidate(**overrides):
    base = {
        "id": "c1",
        "name": "Test Biz",
        "name_normalized": "test_biz",
        "address": "123 Main St, Miami, FL",
        "city": "Miami",
        "city_normalized": "miami",
        "state": "FL",
        "country": "US",
        "phone_raw": "305-555-0001",
        "email_raw": "info@testbiz.com",
        "email_source": "html",
        "website": "https://testbiz.com",
        "source_id": "pid_1",
        "status": "deduped",
        "has_website": True,
        "needs_website": False,
        "needs_redesign": True,
        "needs_chatbot": True,
        "needs_ai_integration": True,
        "dedup_key": "test_biz|3055550001",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestVerifyCandidates:
    def test_basic_verification(self):
        candidates = [_make_candidate()]
        result = verify_candidates(
            candidates,
            hunter_client=FakeHunter(),
            apollo_client=FakeApollo(),
            batch_id="b1",
        )
        assert len(result) == 1
        lead = result[0]
        assert lead["name"] == "Test Biz"
        assert lead["email"] == "info@testbiz.com"
        assert lead["email_verified"] is True
        assert lead["email_confidence"] > 0
        assert lead["needs_score"] >= 0
        assert lead["lead_quality_score"] > 0
        assert lead["verification_batch_id"] == "b1"
        assert "hunter" in lead["verification_sources"]
        assert "apollo" in lead["verification_sources"]

    def test_no_enrichment_clients(self):
        candidates = [_make_candidate()]
        result = verify_candidates(candidates)
        assert len(result) == 1
        lead = result[0]
        assert lead["name"] == "Test Biz"
        assert lead["verification_sources"] == []
        assert lead["email_confidence"] == 0

    def test_candidate_without_email(self):
        candidates = [_make_candidate(email_raw=None)]
        result = verify_candidates(
            candidates,
            hunter_client=FakeHunter(),
        )
        assert len(result) == 1
        lead = result[0]
        assert lead["email"] is None
        assert lead["email_verified"] is False

    def test_candidate_without_website(self):
        candidates = [_make_candidate(website=None, has_website=False)]
        result = verify_candidates(
            candidates,
            apollo_client=FakeApollo(),
        )
        assert len(result) == 1

    def test_multiple_candidates(self):
        candidates = [
            _make_candidate(id="c1", name="Biz A"),
            _make_candidate(id="c2", name="Biz B"),
            _make_candidate(id="c3", name="Biz C"),
        ]
        result = verify_candidates(
            candidates,
            hunter_client=FakeHunter(),
            apollo_client=FakeApollo(),
            batch_id="b1",
        )
        assert len(result) == 3
        assert all(lead["verification_batch_id"] == "b1" for lead in result)

    def test_provenance_populated(self):
        candidates = [_make_candidate()]
        result = verify_candidates(
            candidates,
            hunter_client=FakeHunter(),
            apollo_client=FakeApollo(),
        )
        lead = result[0]
        assert "hunter" in lead["provenance"]
        assert "apollo" in lead["provenance"]

    def test_candidate_ids_from_id(self):
        candidates = [_make_candidate(id="abc-123")]
        result = verify_candidates(candidates)
        assert result[0]["candidate_ids"] == ["abc-123"]

    def test_candidate_without_id(self):
        c = _make_candidate()
        del c["id"]
        result = verify_candidates([c])
        assert result[0]["candidate_ids"] == []

    def test_dedup_key_preserved(self):
        candidates = [_make_candidate(dedup_key="test_biz|3055550001")]
        result = verify_candidates(candidates)
        assert result[0]["dedup_key"] == "test_biz|3055550001"
