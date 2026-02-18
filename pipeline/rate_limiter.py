"""Sliding-window rate limiter for API calls.

Uses time.monotonic() for clock-skew-safe timing.
"""

import time
from collections import defaultdict


class RateLimitExceeded(Exception):
    """Raised when a rate limit is exceeded and wait=False."""


class RateLimiter:
    """Sliding-window rate limiter.

    Args:
        max_calls: Maximum number of calls allowed in the window.
        period_seconds: Length of the sliding window in seconds.
        wait: If True, sleep until a slot is available instead of raising.
    """

    def __init__(self, max_calls: int, period_seconds: float, wait: bool = False):
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self.wait = wait
        self._timestamps: dict[str, list[float]] = defaultdict(list)

    def _prune(self, key: str, now: float) -> None:
        cutoff = now - self.period_seconds
        self._timestamps[key] = [
            t for t in self._timestamps[key] if t > cutoff
        ]

    def acquire(self, key: str = "default") -> None:
        """Acquire a rate limit slot.

        Raises RateLimitExceeded if wait=False and the limit is exceeded.
        Sleeps until a slot opens if wait=True.
        """
        now = time.monotonic()
        self._prune(key, now)

        if len(self._timestamps[key]) < self.max_calls:
            self._timestamps[key].append(now)
            return

        if not self.wait:
            raise RateLimitExceeded(
                f"Rate limit exceeded for '{key}': "
                f"{self.max_calls} calls per {self.period_seconds}s"
            )

        # Wait until the oldest call expires
        oldest = self._timestamps[key][0]
        sleep_time = self.period_seconds - (now - oldest)
        if sleep_time > 0:
            time.sleep(sleep_time)

        now = time.monotonic()
        self._prune(key, now)
        self._timestamps[key].append(now)
