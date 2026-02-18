import pytest
import requests

from leadgen.website_fetch import fetch_html


class DummyResponse:
    """Simple stand-in for requests.Response for testing."""
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text


def test_fetch_html_returns_text_on_200(monkeypatch):
    """For a 200 OK response, fetch_html should return the response text."""

    def fake_get(url, timeout=10, headers=None):
        assert url == "https://example.com"
        # we don't care about exact headers/timeout here, just that call works
        return DummyResponse(status_code=200, text="<html>Hello</html>")

    monkeypatch.setattr(requests, "get", fake_get)

    result = fetch_html("https://example.com")
    assert result == "<html>Hello</html>"


def test_fetch_html_returns_none_for_non_200(monkeypatch):
    """Non-200 responses (e.g. 404, 500) should return None."""

    def fake_get(url, timeout=10, headers=None):
        return DummyResponse(status_code=404, text="Not found")

    monkeypatch.setattr(requests, "get", fake_get)

    result = fetch_html("https://does-not-exist.com")
    assert result is None


def test_fetch_html_returns_none_on_timeout(monkeypatch):
    """Timeouts should be caught and return None, not raise to the caller."""

    def fake_get(url, timeout=10, headers=None):
        raise requests.Timeout("connection timed out")

    monkeypatch.setattr(requests, "get", fake_get)

    result = fetch_html("https://slow-site.com")
    assert result is None


def test_fetch_html_returns_none_on_request_exception(monkeypatch):
    """Generic RequestException (bad URL, DNS issues, etc.) should return None."""

    def fake_get(url, timeout=10, headers=None):
        raise requests.RequestException("some network error")

    monkeypatch.setattr(requests, "get", fake_get)

    result = fetch_html("not-a-valid-url")
    assert result is None
