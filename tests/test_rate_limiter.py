"""Tests for pipeline/rate_limiter.py -- sliding-window rate limiter."""

import time

import pytest

from pipeline.rate_limiter import RateLimiter, RateLimitExceeded


class TestRateLimiter:
    def test_allows_within_limit(self):
        rl = RateLimiter(max_calls=3, period_seconds=1.0)
        for _ in range(3):
            rl.acquire("test")

    def test_raises_when_exceeded(self):
        rl = RateLimiter(max_calls=2, period_seconds=1.0)
        rl.acquire("test")
        rl.acquire("test")
        with pytest.raises(RateLimitExceeded):
            rl.acquire("test")

    def test_different_keys_independent(self):
        rl = RateLimiter(max_calls=1, period_seconds=1.0)
        rl.acquire("a")
        rl.acquire("b")  # Different key, should work

    def test_default_key(self):
        rl = RateLimiter(max_calls=1, period_seconds=1.0)
        rl.acquire()
        with pytest.raises(RateLimitExceeded):
            rl.acquire()

    def test_window_slides(self):
        rl = RateLimiter(max_calls=1, period_seconds=0.05)
        rl.acquire("test")
        with pytest.raises(RateLimitExceeded):
            rl.acquire("test")
        time.sleep(0.06)
        rl.acquire("test")  # Window expired, should work

    def test_wait_mode(self):
        rl = RateLimiter(max_calls=1, period_seconds=0.05, wait=True)
        rl.acquire("test")
        start = time.monotonic()
        rl.acquire("test")  # Should sleep instead of raising
        elapsed = time.monotonic() - start
        assert elapsed >= 0.04  # Slept for ~0.05s

    def test_error_message_contains_details(self):
        rl = RateLimiter(max_calls=5, period_seconds=60.0)
        for _ in range(5):
            rl.acquire("api")
        with pytest.raises(RateLimitExceeded, match="api"):
            rl.acquire("api")
