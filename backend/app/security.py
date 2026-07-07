import secrets
import time

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .auth import ACCESS_COOKIE, CSRF_COOKIE, CSRF_HEADER
from .config import app_settings
from .proxy import client_ip


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


# Broad per-IP throttle applied to every /api request by RateLimitMiddleware.
global_limiter = SlidingWindowRateLimiter(
    app_settings.global_rate_limit_max,
    app_settings.global_rate_limit_window,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Broad per-IP request throttle for the API surface.

    Counts every ``/api`` request (except the health check) against a shared
    sliding-window limiter keyed on the trusted-proxy aware client IP, so a
    client behind a declared reverse proxy is throttled on its real address and
    cannot escape it by forging ``X-Forwarded-For``.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api") and path != "/api/health":
            try:
                global_limiter.check(f"global:{client_ip(request)}")
            except HTTPException as exc:
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail},
                    headers=exc.headers,
                )
        return await call_next(request)


class CsrfMiddleware(BaseHTTPMiddleware):
    """Double-submit-cookie CSRF protection for cookie-authenticated requests.

    For unsafe methods on /api routes, when the session is carried by the
    HttpOnly cookie, require the ``X-CSRF-Token`` header to match the readable
    ``csrf_token`` cookie. Requests authenticated purely via the Bearer header
    (no session cookie) are not vulnerable to CSRF and are left untouched.
    """

    SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

    async def dispatch(self, request: Request, call_next):
        if (
            request.method not in self.SAFE_METHODS
            and request.url.path.startswith("/api")
            and request.cookies.get(ACCESS_COOKIE)
        ):
            header_token = request.headers.get(CSRF_HEADER, "")
            cookie_token = request.cookies.get(CSRF_COOKIE, "")
            if (
                not header_token
                or not cookie_token
                or not secrets.compare_digest(header_token, cookie_token)
            ):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token missing or invalid"},
                )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every HTTP response."""

    FONT_GOOGLE = "https://fonts.gstatic.com"

    # Build CSP once at class level — one directive per list entry, auditable.
    # Swagger UI assets are self-hosted (see main.py), so no third-party CDN is
    # allowed in script-src/style-src.
    _CSP_DIRECTIVES: list[str] = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline'",  # Angular requires unsafe-inline
        "style-src 'self' 'unsafe-inline'",  # Bootstrap inline styles
        "img-src 'self' data: https:",  # logos, QR codes base64
        f"font-src 'self' data: {FONT_GOOGLE}",  # Bootstrap Icons embedded font
        "connect-src 'self'",  # API calls + Azure endpoints
        "worker-src 'self'",  # Angular Service Worker (PWA)
        "frame-ancestors 'none'",  # replaces X-Frame-Options
    ]
    _CSP: str = "; ".join(_CSP_DIRECTIVES) + ";"

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = self._CSP
        return response
