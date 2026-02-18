import types

import pytest

from leadgen import places


class FakeResp:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


def _make_results(count, offset=0):
    return [{"name": f"Biz{offset + i}", "place_id": f"pid{offset + i}"} for i in range(count)]


def _make_page(results, token=None, status="OK"):
    payload = {"status": status, "results": results}
    if token:
        payload["next_page_token"] = token
    return payload


@pytest.fixture
def fake_sleep(monkeypatch):
    calls = []

    def _fake_sleep(seconds):
        calls.append(seconds)

    return calls, _fake_sleep


def test_places_limit_20_single_page(monkeypatch, fake_sleep):
    calls, sleep_fn = fake_sleep
    responses = [FakeResp(_make_page(_make_results(20), token="token1"))]

    def fake_request(url, params, *, _sleep, _max_attempts):
        return responses.pop(0) if responses else None

    monkeypatch.setattr(places, "_request_with_retry", fake_request)
    results = places.search_places("q", limit=20, _sleep=sleep_fn)
    assert len(results) == 20
    assert calls == []  # no pagination sleep


def test_places_limit_25_two_pages(monkeypatch, fake_sleep):
    calls, sleep_fn = fake_sleep
    responses = [
        FakeResp(_make_page(_make_results(20), token="token1")),
        FakeResp(_make_page(_make_results(10, offset=20), token=None)),
    ]

    def fake_request(url, params, *, _sleep, _max_attempts):
        return responses.pop(0) if responses else None

    monkeypatch.setattr(places, "_request_with_retry", fake_request)
    results = places.search_places("q", limit=25, _sleep=sleep_fn)
    assert len(results) == 25  # 20 + 5 from second page
    assert len(calls) == 1  # one sleep between pages


def test_places_limit_100_only_35_available(monkeypatch, fake_sleep):
    calls, sleep_fn = fake_sleep
    responses = [
        FakeResp(_make_page(_make_results(20), token="t1")),
        FakeResp(_make_page(_make_results(10, offset=20), token="t2")),
        FakeResp(_make_page(_make_results(5, offset=30), token=None)),
    ]

    def fake_request(url, params, *, _sleep, _max_attempts):
        return responses.pop(0) if responses else None

    monkeypatch.setattr(places, "_request_with_retry", fake_request)
    results = places.search_places("q", limit=100, _sleep=sleep_fn)
    assert len(results) == 35
    assert len(calls) == 2  # slept between first-second and second-third


def test_places_limit_capped_by_max(monkeypatch, fake_sleep):
    calls, sleep_fn = fake_sleep
    monkeypatch.setattr(places, "MAX_PLACES_RESULTS", 40)
    responses = [
        FakeResp(_make_page(_make_results(20), token="t1")),
        FakeResp(_make_page(_make_results(20, offset=20), token="t2")),
        FakeResp(_make_page(_make_results(20, offset=40), token=None)),
    ]

    def fake_request(url, params, *, _sleep, _max_attempts):
        return responses.pop(0) if responses else None

    monkeypatch.setattr(places, "_request_with_retry", fake_request)
    results = places.search_places("q", limit=1000, _sleep=sleep_fn)
    # capped to 40, should not fetch beyond that even if more pages exist
    assert len(results) == 40
    # only two pages needed to reach cap (20 + 20)
    assert len(calls) == 1


def test_places_quota_error_second_page(monkeypatch, fake_sleep):
    calls, sleep_fn = fake_sleep
    responses = [
        FakeResp(_make_page(_make_results(20), token="t1")),
        FakeResp(_make_page([], token=None, status="OVER_QUERY_LIMIT"), status_code=429),
    ]

    def fake_request(url, params, *, _sleep, _max_attempts):
        return responses.pop(0) if responses else None

    monkeypatch.setattr(places, "_request_with_retry", fake_request)
    results = places.search_places("q", limit=40, _sleep=sleep_fn)
    assert len(results) == 20  # only first page collected
    assert len(calls) == 1  # attempted pagination sleep before second request
