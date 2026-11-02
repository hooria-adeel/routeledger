import os
import threading
import time
from collections import defaultdict, deque
from urllib.parse import urlsplit

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import settings

# The automatic documentation pages load their design from outside, so the
# strictest header (Content-Security-Policy) is not applied to them.
DOC_PATHS = ("/docs", "/redoc", "/openapi.json")

# Everything starting with these is data (JSON). Everything else is a web page.
API_PATHS = ("/auth", "/products", "/retailers", "/branches", "/areas", "/orders",
             "/dashboard", "/employees", "/activity-log", "/health")

# Rules for the pages themselves: only our own files may run or load, nothing
# from other websites, and nobody can put the app inside a hidden frame.
PAGE_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; "
    "frame-ancestors 'none'"
)

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# Hosts that the browser is allowed to send state-changing requests from.
# A same-origin POST sends an Origin header, so an unknown Origin means the
# request came from another website (CSRF). This is a second line of defence
# next to SameSite cookies and CORS.
ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in settings.cors_origins.split(",")
    if origin.strip()
}


def cors_origins() -> list[str]:
    """Configured origins, plus the platform URL when the host tells us one.

    Render, Fly.io, Railway and Vercel all expose the public hostname in an
    environment variable. Adding it automatically keeps the deployment
    configuration shorter and avoids a broken first deploy.
    """
    origins = list(ALLOWED_ORIGINS)
    for variable in ("RENDER_EXTERNAL_HOSTNAME", "FLY_APP_NAME"):
        host = os.environ.get(variable)
        if host and variable == "RENDER_EXTERNAL_HOSTNAME":
            origins.append(f"https://{host}")
        elif host and variable == "FLY_APP_NAME":
            origins.append(f"https://{host}.fly.dev")
    for variable in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
        host = os.environ.get(variable)
        if host:
            origins.append(f"https://{host}")
    return sorted(set(origins))


def allowed_hosts() -> list[str]:
    """Configured hostnames plus the platform hostname, for TrustedHostMiddleware."""
    hosts = {h.strip() for h in settings.allowed_hosts.split(",") if h.strip()}
    host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if host:
        hosts.add(host)
    for variable in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
        host = os.environ.get(variable)
        if host:
            hosts.add(host)
    # Vercel preview deployments get a new *.vercel.app name on every commit.
    if os.environ.get("VERCEL"):
        hosts.add("*.vercel.app")
    return sorted(hosts)


async def add_security_headers(request: Request, call_next):
    """Adds protective headers to every answer the backend sends."""
    response = await call_next(request)
    path = request.url.path
    response.headers["X-Content-Type-Options"] = "nosniff"        # browser must not guess file types
    response.headers["X-Frame-Options"] = "DENY"                  # nobody can embed us in a hidden frame
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    if not path.startswith(DOC_PATHS):
        if path.startswith(API_PATHS):
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
            response.headers["Cache-Control"] = "no-store"        # private data is never cached
        else:
            response.headers["Content-Security-Policy"] = PAGE_POLICY
            response.headers["Cache-Control"] = "no-cache"        # always check for a newer version
    if settings.cookie_secure:                                    # only when the site runs on https
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


async def check_request_origin(request: Request, call_next):
    """Refuses state-changing requests that come from another website.

    Login cookies are SameSite=Lax, but that alone is not enough for older
    browsers. Rejecting an unexpected Origin header closes the CSRF gap
    without needing a token in every form.
    """
    if request.method not in SAFE_METHODS:
        origin = request.headers.get("origin")
        fetch_site = request.headers.get("sec-fetch-site")
        if origin:
            # A same-origin request is always fine; a cross-origin one is only
            # fine when the site is explicitly configured.
            same_host = urlsplit(origin).netloc == request.url.netloc
            if not same_host and origin.rstrip("/") not in ALLOWED_ORIGINS:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Cross-site request blocked."},
                )
        if fetch_site == "cross-site":
            return JSONResponse(
                status_code=403,
                content={"detail": "Cross-site request blocked."},
            )
    return await call_next(request)


class RateLimiter:
    """Allows only a few requests per minute from one computer (IP address).
    It remembers in the app's memory, which is fine for one server. Larger
    systems keep this in Redis instead."""

    def __init__(self, max_calls: int, per_seconds: int):
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self.calls = defaultdict(deque)
        self.lock = threading.Lock()

    def __call__(self, request: Request):
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        with self.lock:
            recent = self.calls[key]
            while recent and now - recent[0] > self.per_seconds:
                recent.popleft()
            if len(recent) >= self.max_calls:
                wait = int(self.per_seconds - (now - recent[0])) + 1
                raise HTTPException(
                    status_code=429,
                    detail="Too many attempts. Please wait a moment and try again.",
                    headers={"Retry-After": str(wait)},
                )
            recent.append(now)


# Login: at most 10 tries per minute from one computer
login_limiter = RateLimiter(max_calls=10, per_seconds=60)
