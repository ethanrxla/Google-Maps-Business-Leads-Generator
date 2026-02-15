from collections import Counter

from csv_supabase_backfill import _coverage_percentages, enrich_verified_row_from_candidates


def test_patch_fills_missing_fields_in_required_order():
    verified = {
        "address": None,
        "city": "",
        "phone": "",
        "email": None,
        "website": "",
    }
    candidates = [
        {
            "address": "  ",
            "city": "Miami",
            "phone_raw": "",
            "email_raw": "first@example.com",
            "website": "",
        },
        {
            "address": "123 Ocean Dr",
            "city": "Fort Lauderdale",
            "phone_raw": "+1-555-0100",
            "email_raw": "second@example.com",
            "website": "https://example.com",
        },
    ]

    patched, updated = enrich_verified_row_from_candidates(verified, candidates)

    assert patched["address"] == "123 Ocean Dr"
    assert patched["city"] == "Miami"
    assert patched["phone"] == "+1-555-0100"
    assert patched["email"] == "first@example.com"
    assert patched["website"] == "https://example.com"
    assert updated == ["address", "city", "phone", "email", "website"]


def test_patch_is_idempotent_and_never_overwrites_non_empty_values():
    verified = {
        "address": "Existing Address",
        "city": "Existing City",
        "phone": "Existing Phone",
        "email": "existing@example.com",
        "website": "https://existing.example",
    }
    candidates = [
        {
            "address": "New Address",
            "city": "New City",
            "phone_raw": "New Phone",
            "email_raw": "new@example.com",
            "website": "https://new.example",
        }
    ]

    patched_once, updated_once = enrich_verified_row_from_candidates(verified, candidates)
    patched_twice, updated_twice = enrich_verified_row_from_candidates(patched_once, candidates)

    assert patched_once == verified
    assert updated_once == []
    assert patched_twice == patched_once
    assert updated_twice == []


def test_candidate_order_is_deterministic_for_conflicting_values():
    verified = {
        "address": "",
        "city": "",
        "phone": "",
        "email": "",
        "website": "",
    }
    candidates = [
        {
            "address": "111 First St",
            "city": "City One",
            "phone_raw": "111-1111",
            "email_raw": "one@example.com",
            "website": "https://one.example",
        },
        {
            "address": "222 Second St",
            "city": "City Two",
            "phone_raw": "222-2222",
            "email_raw": "two@example.com",
            "website": "https://two.example",
        },
    ]

    patched, updated = enrich_verified_row_from_candidates(verified, candidates)

    assert patched == {
        "address": "111 First St",
        "city": "City One",
        "phone": "111-1111",
        "email": "one@example.com",
        "website": "https://one.example",
    }
    assert updated == ["address", "city", "phone", "email", "website"]


def test_coverage_percentages_smoke():
    counts = Counter({"address": 3, "city": 1, "phone": 0, "email": 2, "website": 3})
    pct = _coverage_percentages(counts, total_rows=4)

    assert pct == {
        "address": 75.0,
        "city": 25.0,
        "phone": 0.0,
        "email": 50.0,
        "website": 75.0,
    }
