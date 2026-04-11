from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every HTTP response."""

    JSDELIVR = "https://cdn.jsdelivr.net/npm/"

    # Build CSP once at class level — one directive per list entry, auditable.
    _CSP_DIRECTIVES: list[str] = [
        "default-src 'self'",
        f"script-src 'self' 'unsafe-inline' {JSDELIVR}",  # Angular requires unsafe-inline
        f"style-src 'self' 'unsafe-inline' {JSDELIVR}",  # Bootstrap inline styles
        "img-src 'self' data: https:",  # logos, QR codes base64
        "font-src 'self' data:",  # Bootstrap Icons embedded font
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
