"""In-memory sliding-window rate limiter for authentication endpoints."""

from __future__ import annotations

import time

from fastapi import HTTPException, Request, status

from ..config import app_settings
from ..proxy import client_ip


class SlidingWindowRateLimiter:
    """Track request timestamps per key within a fixed time window.

    Suitable for the single-worker deployment this image ships with. For a
    multi-process or multi-replica setup, back this with a shared store such
    as Redis instead.
    """

    _PRUNE_THRESHOLD = 1024

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}

    def _prune(self, cutoff: float) -> None:
        """Drop keys whose recorded hits have all fallen outside the window."""
        for key in list(self._hits):
            fresh = [t for t in self._hits[key] if t > cutoff]
            if fresh:
                self._hits[key] = fresh
            else:
                del self._hits[key]

    def check(self, key: str) -> None:
        """Record a hit for ``key``; raise HTTP 429 once the limit is exceeded."""
        now = time.monotonic()
        cutoff = now - self.window_seconds

        if len(self._hits) > self._PRUNE_THRESHOLD:
            self._prune(cutoff)

        hits = [t for t in self._hits.get(key, ()) if t > cutoff]
        if len(hits) >= self.max_requests:
            self._hits[key] = hits
            retry_after = max(int(self.window_seconds - (now - hits[0])) + 1, 1)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

        hits.append(now)
        self._hits[key] = hits


_login_limiter = SlidingWindowRateLimiter(
    app_settings.login_rate_limit_max,
    app_settings.login_rate_limit_window,
)


def _client_ip(request: Request) -> str:
    """Return the originating client IP address of the request.

    Delegates to the trusted-proxy aware helper so per-IP throttling targets the
    real client only when ``X-Forwarded-For`` comes from a trusted proxy.
    """
    return client_ip(request)


async def login_rate_limit(request: Request) -> None:
    """FastAPI dependency: throttle repeated auth attempts per client IP."""
    _login_limiter.check(f"login:{_client_ip(request)}")
