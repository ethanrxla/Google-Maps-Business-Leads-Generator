"""Tests for pipeline/deduper.py -- dedupe key computation and candidate dedup."""

import pytest

from pipeline.deduper import (
    compute_dedupe_key,
    dedupe_candidates,
    normalize_name,
)


# ---------------------------------------------------------------------------
# normalize_name
# ---------------------------------------------------------------------------

class TestNormalizeName:
    def test_lowercase(self):
        assert normalize_name("ACME Corp") == "acme"

    def test_strips_llc(self):
        assert normalize_name("Smith LLC") == "smith"

    def test_strips_inc(self):
        assert normalize_name("BigCo Inc") == "bigco"

    def test_strips_multiple_suffixes(self):
        assert normalize_name("Jones Corp LLC") == "jones"

    def test_collapses_non_alnum(self):
        assert normalize_name("Bob's Plumbing & Heating") == "bob_s_plumbing_heating"

    def test_empty(self):
        assert normalize_name("") == ""

    def test_whitespace(self):
        assert normalize_name("   ") == ""


# ---------------------------------------------------------------------------
# compute_dedupe_key
# ---------------------------------------------------------------------------

class TestComputeDedupeKey:
    def test_phone_anchor(self):
        key = compute_dedupe_key("Acme Corp", phone="(555) 123-4567")
        assert key == "acme|5551234567"

    def test_website_anchor(self):
        key = compute_dedupe_key("Acme Corp", website="https://acme.com/")
        assert key == "acme|acme.com"

    def test_city_state_anchor(self):
        key = compute_dedupe_key("Acme Corp", city="Miami", state="FL")
        assert key == "acme|miami_fl"

    def test_city_only_anchor(self):
        key = compute_dedupe_key("Acme Corp", city="Miami")
        assert key == "acme|miami"

    def test_phone_preferred_over_website(self):
        key = compute_dedupe_key("Acme", phone="555", website="https://x.com")
        assert "555" in key
        assert "x.com" not in key

    def test_name_only_no_anchor(self):
        key = compute_dedupe_key("Acme Corp")
        assert key == "acme"

    def test_empty_name(self):
        assert compute_dedupe_key("") == ""


# ---------------------------------------------------------------------------
# dedupe_candidates
# ---------------------------------------------------------------------------

class TestDedupeCandidates:
    def test_no_duplicates(self):
        candidates = [
            {"name": "Biz A", "city": "Miami", "status": "new"},
            {"name": "Biz B", "city": "Miami", "status": "new"},
        ]
        kept, dupes = dedupe_candidates(candidates)
        assert len(kept) == 2
        assert len(dupes) == 0
        assert all(c["status"] == "deduped" for c in kept)
        assert all("dedup_key" in c for c in kept)

    def test_exact_duplicates(self):
        candidates = [
            {"name": "Acme Corp", "phone_raw": "555-1234", "status": "new"},
            {"name": "ACME CORP", "phone_raw": "(555) 1234", "status": "new"},
        ]
        kept, dupes = dedupe_candidates(candidates)
        assert len(kept) == 1
        assert len(dupes) == 1
        assert dupes[0]["status"] == "duplicate"

    def test_same_name_different_anchors(self):
        candidates = [
            {"name": "Acme", "city": "Miami", "status": "new"},
            {"name": "Acme", "city": "Tampa", "status": "new"},
        ]
        kept, dupes = dedupe_candidates(candidates)
        assert len(kept) == 2
        assert len(dupes) == 0

    def test_llc_suffix_ignored(self):
        candidates = [
            {"name": "Smith LLC", "city": "Miami", "status": "new"},
            {"name": "Smith", "city": "Miami", "status": "new"},
        ]
        kept, dupes = dedupe_candidates(candidates)
        assert len(kept) == 1
        assert len(dupes) == 1

    def test_empty_list(self):
        kept, dupes = dedupe_candidates([])
        assert kept == []
        assert dupes == []

    def test_dedup_key_set_on_all(self):
        candidates = [
            {"name": "A", "status": "new"},
            {"name": "A", "status": "new"},
            {"name": "B", "status": "new"},
        ]
        kept, dupes = dedupe_candidates(candidates)
        for c in kept + dupes:
            assert "dedup_key" in c


class TestDedupeStage:
    """Integration-level tests with realistic multi-candidate lists."""

    def test_realistic_city_sweep(self):
        candidates = [
            {"name": "Miami Dental LLC", "city": "Miami", "state": "FL",
             "phone_raw": "305-555-0001", "email_raw": "info@miamidental.com",
             "website": "https://miamidental.com", "status": "new"},
            {"name": "Miami Dental", "city": "Miami", "state": "FL",
             "phone_raw": "(305) 555-0001", "email_raw": "contact@miamidental.com",
             "website": "https://miamidental.com", "status": "new"},
            {"name": "Coral Gables Dentistry", "city": "Coral Gables", "state": "FL",
             "phone_raw": "305-555-0002", "email_raw": "info@cgdentistry.com",
             "website": "https://cgdentistry.com", "status": "new"},
            {"name": "Brickell Smiles Inc", "city": "Miami", "state": "FL",
             "phone_raw": "305-555-0003", "email_raw": None,
             "website": "https://brickellsmiles.com", "status": "new"},
            {"name": "BRICKELL SMILES", "city": "Miami", "state": "FL",
             "phone_raw": "305-555-0003", "email_raw": "hello@brickellsmiles.com",
             "website": None, "status": "new"},
        ]
        kept, dupes = dedupe_candidates(candidates)
        assert len(kept) == 3
        assert len(dupes) == 2
        # All kept should be deduped, all dupes should be duplicate
        assert all(c["status"] == "deduped" for c in kept)
        assert all(c["status"] == "duplicate" for c in dupes)

    def test_status_transitions(self):
        candidates = [
            {"name": "A", "city": "X", "status": "new"},
            {"name": "A", "city": "X", "status": "new"},
            {"name": "B", "city": "Y", "status": "new"},
        ]
        kept, dupes = dedupe_candidates(candidates)
        assert kept[0]["status"] == "deduped"
        assert kept[1]["status"] == "deduped"
        assert dupes[0]["status"] == "duplicate"
