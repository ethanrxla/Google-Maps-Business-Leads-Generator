import pytest
import requests

from leadgen.places import search_places, get_details
from leadgen.models import Business


class DummyResponse:
    """Simple fake for requests.Response with configurable JSON payload."""
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data


#
# Tests for search_places()
#

def test_search_places_returns_business_objects(monkeypatch):
    """search_places should return a list of Business instances for a valid query."""

    fake_data = {
        "results": [
            {
                "place_id": "abc123",
                "name": "Cool Pizza",
                "formatted_address": "123 Slice St",
                "website": "https://coolpizza.com",
            }
        ],
        "status": "OK",
    }

    def fake_get(url, params=None, timeout=None):
        # we don't care about url/params in detail, just that it returns our fake_data
        return DummyResponse(fake_data, status_code=200)

    monkeypatch.setattr(requests, "get", fake_get)

    # Your real function signature: search_places(query, limit=20)
    results = search_places("pizza", limit=5)
    assert len(results) == 1

    biz = results[0]
    assert isinstance(biz, Business)
    assert biz.name == "Cool Pizza"
    assert biz.address == "123 Slice St"
    # initial website is None in search_places; get_details() may fill it later
    # if your implementation sets website=None initially:
    # assert biz.website is None or biz.website == "https://coolpizza.com"
    assert biz.place_id == "abc123"


def test_search_places_respects_limit(monkeypatch):
    """search_places should only return up to the 'limit' number of businesses."""

    fake_results = {
        "results": [
            {
                "place_id": f"id{i}",
                "name": f"Biz{i}",
                "formatted_address": f"Addr{i}",
                "website": None,
            }
            for i in range(10)
        ],
        "status": "OK",
    }

    def fake_get(url, params=None, timeout=None):
        return DummyResponse(fake_results, status_code=200)

    monkeypatch.setattr(requests, "get", fake_get)

    results = search_places("shops", limit=3)
    assert len(results) == 3
    assert all(isinstance(b, Business) for b in results)


def test_search_places_handles_zero_results(monkeypatch):
    """If Places returns ZERO_RESULTS / empty list, search_places should return []"""

    fake_results = {
        "results": [],
        "status": "ZERO_RESULTS",
    }

    def fake_get(url, params=None, timeout=None):
        return DummyResponse(fake_results, status_code=200)

    monkeypatch.setattr(requests, "get", fake_get)

    results = search_places("anything")
    assert results == []


def test_search_places_missing_fields(monkeypatch):
    """Missing optional fields (website, formatted_address) should not crash."""

    fake_results = {
        "results": [
            {
                "place_id": "xyz",
                "name": "Mystery Biz",
                # no website
                # no formatted_address
            }
        ],
        "status": "OK",
    }

    def fake_get(url, params=None, timeout=None):
        return DummyResponse(fake_results, status_code=200)

    monkeypatch.setattr(requests, "get", fake_get)

    results = search_places("mystery")
    assert len(results) == 1
    biz = results[0]

    assert biz.name == "Mystery Biz"
    # Depending on your implementation, these will likely be None
    assert biz.website is None
    assert biz.address is None


def test_search_places_handles_non_ok_status(monkeypatch):
    """Any non-OK status with empty results should produce an empty list."""

    fake_results = {
        "results": [],
        "status": "OVER_QUERY_LIMIT",
    }

    def fake_get(url, params=None, timeout=None):
        return DummyResponse(fake_results, status_code=200)

    monkeypatch.setattr(requests, "get", fake_get)

    results = search_places("query")
    assert results == []


#
# Tests for get_details()
#

def test_get_details_populates_fields(monkeypatch):
    """get_details should update website + address when Places details returns them."""

    biz = Business(
        name="Test",
        address=None,
        website=None,
        phone=None,
        email=None,
        place_id="abc123",
    )

    fake_details = {
        "result": {
            "website": "https://updated.com",
            "formatted_address": "555 Updated Lane",
            "formatted_phone_number": "(555) 123-4567",
            "email": "info@updated.com",
        }
    }

    def fake_get(url, params=None, timeout=None):
        # You can assert on params["place_id"] == "abc123" if you want stricter tests
        return DummyResponse(fake_details, status_code=200)

    monkeypatch.setattr(requests, "get", fake_get)

    updated = get_details(biz)

    assert updated.website == "https://updated.com"
    assert updated.address == "555 Updated Lane"
    assert updated.phone == "(555) 123-4567"
    assert updated.email == "info@updated.com"


def test_get_details_handles_missing_fields(monkeypatch):
    """Missing website or formatted_address should not crash and leave them as None."""

    biz = Business(
        name="Test",
        address=None,
        website=None,
        phone=None,
        email=None,
        place_id="abc123",
    )

    fake_details = {
        "result": {
            # website missing
            # formatted_address missing
        }
    }

    def fake_get(url, params=None, timeout=None):
        return DummyResponse(fake_details, status_code=200)

    monkeypatch.setattr(requests, "get", fake_get)

    updated = get_details(biz)
    assert updated.website is None
    assert updated.address is None
    assert updated.phone is None
    assert updated.email is None


def test_get_details_prefers_formatted_phone(monkeypatch):
    """If phone numbers exist, use the formatted one, else fall back to international."""

    biz = Business(
        name="Phoney",
        address=None,
        website=None,
        phone=None,
        email=None,
        place_id="abc123",
    )

    fake_details = {
        "result": {
            "international_phone_number": "+1 555-000-0000",
        }
    }

    def fake_get(url, params=None, timeout=None):
        return DummyResponse(fake_details, status_code=200)

    monkeypatch.setattr(requests, "get", fake_get)

    updated = get_details(biz)
    assert updated.phone == "+1 555-000-0000"


def test_get_details_gracefully_handles_missing_place_id(monkeypatch):
    """If place_id is None, get_details should just return the business unchanged."""

    biz = Business(
        name="NoID",
        address=None,
        website=None,
        place_id=None,
    )

    # If implementation is correct, requests.get should NOT be called.
    def fake_get(url, params=None, timeout=None):
        raise AssertionError("requests.get should not be called when place_id is None")

    monkeypatch.setattr(requests, "get", fake_get)

    updated = get_details(biz)
    assert updated is biz
    assert updated.place_id is None
