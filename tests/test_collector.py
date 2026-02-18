"""Tests for pipeline/collector.py -- candidate collection stage."""

import pytest

from leadgen.models import Business
from pipeline.collector import _normalize_city, collect_candidates


class TestNormalizeCity:
    def test_full_address(self):
        assert _normalize_city("123 Main St, Miami, FL 33101, USA") == "miami"

    def test_city_state_country(self):
        assert _normalize_city("Miami, FL, USA") == "miami"

    def test_city_state(self):
        assert _normalize_city("Miami, FL") == "miami"

    def test_none(self):
        assert _normalize_city(None) is None

    def test_empty(self):
        assert _normalize_city("") is None


class FakeAnalysis:
    def __init__(self):
        self.has_website = True
        self.needs_website = False
        self.needs_redesign = False
        self.needs_chatbot = True
        self.needs_ai_integration = True
        self.raw_data = {}


class TestCollectCandidates:
    def _make_businesses(self, count=3):
        return [
            Business(
                name=f"Biz {i}",
                address=f"{i}00 Main St, Miami, FL",
                website=f"https://biz{i}.com",
                phone=f"555-000{i}",
                place_id=f"pid_{i}",
            )
            for i in range(count)
        ]

    def test_basic_collection(self, monkeypatch):
        businesses = self._make_businesses(2)

        monkeypatch.setattr(
            "pipeline.collector.search_places",
            lambda query, limit, include_status: (businesses, "OK"),
        )
        monkeypatch.setattr(
            "pipeline.collector.get_details",
            lambda biz: biz,
        )
        monkeypatch.setattr(
            "pipeline.collector.fetch_html",
            lambda url: "<html><body>Hello</body></html>",
        )
        monkeypatch.setattr(
            "pipeline.collector.extract_emails",
            lambda html: ["info@biz.com"],
        )
        monkeypatch.setattr(
            "pipeline.collector.analyze_html",
            lambda html: FakeAnalysis(),
        )

        candidates, status = collect_candidates("dentists Miami", limit=2, batch_id="b1")

        assert status == "OK"
        assert len(candidates) == 2
        assert candidates[0]["name"] == "Biz 0"
        assert candidates[0]["source"] == "google_places"
        assert candidates[0]["collection_batch_id"] == "b1"
        assert candidates[0]["status"] == "new"
        assert candidates[0]["name_normalized"] != ""
        assert candidates[0]["email_raw"] == "info@biz.com"

    def test_no_results(self, monkeypatch):
        monkeypatch.setattr(
            "pipeline.collector.search_places",
            lambda query, limit, include_status: ([], "ZERO_RESULTS"),
        )

        candidates, status = collect_candidates("nonexistent", limit=10)
        assert candidates == []
        assert status == "ZERO_RESULTS"

    def test_no_website(self, monkeypatch):
        biz = Business(name="No Web", address="Miami, FL", place_id="pid")
        monkeypatch.setattr(
            "pipeline.collector.search_places",
            lambda query, limit, include_status: ([biz], "OK"),
        )
        monkeypatch.setattr(
            "pipeline.collector.get_details",
            lambda biz: biz,
        )
        monkeypatch.setattr(
            "pipeline.collector.analyze_html",
            lambda html: FakeAnalysis(),
        )

        candidates, status = collect_candidates("test", limit=1)
        assert len(candidates) == 1
        assert candidates[0]["website"] is None
        assert candidates[0]["email_raw"] is None
