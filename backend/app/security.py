import secrets

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .auth import ACCESS_COOKIE, CSRF_COOKIE, CSRF_HEADER


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
