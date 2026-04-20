"""
Middleware — request-level processing that runs on every request.

Currently includes:
  - Rate limiting: prevents abuse by limiting requests per IP
  - Security headers: adds standard security headers to all responses

These run BEFORE route handlers, so they protect the entire API.
"""

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from hts_oracle.config import get_settings


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
# Simple in-memory rate limiter. Tracks request counts per IP address
# in a sliding time window.
#
# For a single-process deployment (Render/Railway with 1 worker), this
# is fine. For multi-worker, you'd use Redis instead.

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Limits requests per IP address.

    Default: 60 requests per 60-second window.
    When exceeded, returns 429 Too Many Requests.

    Health checks (/api/v1/health) are exempt — monitoring tools
    hit this endpoint frequently and shouldn't be rate limited.
    """

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # { ip_address: [timestamp1, timestamp2, ...] }
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.endswith("/health"):
            return await call_next(request)

        # Get client IP (X-Forwarded-For if behind a proxy, else direct IP)
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"

        now = time.time()
        window_start = now - self.window_seconds

        # Remove timestamps outside the current window
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]

        # Check if over the limit
        if len(self._requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
            )

        # Record this request
        self._requests[client_ip].append(now)

        return await call_next(request)


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds standard security headers to all responses.

    These protect against common web attacks:
      - X-Content-Type-Options: prevents MIME sniffing
      - X-Frame-Options: prevents clickjacking
      - Referrer-Policy: limits referrer info leakage
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
