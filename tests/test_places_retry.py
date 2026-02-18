import requests

from leadgen import places
from leadgen.models import Business


class DummyResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data


def test_search_places_retries_and_succeeds(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append(1)
        if len(calls) < 3:
            raise requests.RequestException("transient")
        return DummyResponse(
            {
                "results": [
                    {
                        "place_id": "pid1",
                        "name": "Retried Biz",
                        "formatted_address": "123 Retry Rd",
                    }
                ],
                "status": "OK",
            },
            status_code=200,
        )

    monkeypatch.setattr(places.requests, "get", fake_get)

    results = places.search_places(
        "query", _sleep=lambda _: None, _max_attempts=3
    )

    assert len(calls) == 3
    assert len(results) == 1
    assert isinstance(results[0], Business)
    assert results[0].name == "Retried Biz"


def test_search_places_retries_and_returns_empty_on_failure(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append(1)
        raise requests.RequestException("fail")

    monkeypatch.setattr(places.requests, "get", fake_get)

    results, status = places.search_places(
        "query", include_status=True, _sleep=lambda _: None, _max_attempts=2
    )

    assert len(calls) == 2
    assert results == []
    assert status == "ERROR"
