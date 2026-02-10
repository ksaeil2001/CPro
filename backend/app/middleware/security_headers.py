"""Security headers middleware."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses.

    Headers added:
    - X-Frame-Options: Prevents clickjacking
    - X-Content-Type-Options: Prevents MIME sniffing
    - X-XSS-Protection: Enables XSS filter in older browsers
    - Strict-Transport-Security: Enforces HTTPS
    - Content-Security-Policy: Controls resource loading
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Enforce HTTPS (only in production with HTTPS)
        # Note: Disabled in development to allow HTTP
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy (restrictive)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: blob:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self';"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response
