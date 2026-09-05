"""Shared server-side security primitives for the Parivahan services.

Deliberately stdlib-only (hmac, hashlib, base64, time) so every service can
import it without new dependencies. Two auth models:

  * SESSION tokens — bind a browser session to one applicant_id (HMAC-signed,
    with expiry). Journey mints them; every /journey/{id}/* call verifies the
    token AND that its applicant_id matches the path (ownership → closes IDOR).
  * SERVICE tokens — a shared secret for service-to-service calls (journey →
    gateway, journey → identity), so a citizen's browser can never hit the
    government endpoints directly.

Secrets come from the environment. The dev defaults let the prototype run out
of the box; production MUST override them (documented in .env.example / README).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time

_DEV_SESSION_SECRET = "parivahan-dev-session-secret-change-in-prod"
_DEV_SERVICE_TOKEN = "parivahan-dev-service-token-change-in-prod"

SESSION_TTL_SECONDS = int(os.environ.get("PARIVAHAN_SESSION_TTL", "3600"))


def _session_secret() -> bytes:
    return os.environ.get("PARIVAHAN_SESSION_SECRET", _DEV_SESSION_SECRET).encode()


def service_token() -> str:
    return os.environ.get("PARIVAHAN_SERVICE_TOKEN", _DEV_SERVICE_TOKEN)


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def mint_session(applicant_id: str, ttl: int | None = None, now: float | None = None) -> str:
    """Create an HMAC-signed session token bound to applicant_id."""
    exp = int((now if now is not None else time.time()) + (ttl or SESSION_TTL_SECONDS))
    payload = f"{applicant_id}|{exp}"
    sig = hmac.new(_session_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{_b64(payload.encode())}.{sig}"


def verify_session(token: str | None, now: float | None = None) -> str | None:
    """Return the applicant_id if the token is valid and unexpired, else None."""
    if not token:
        return None
    token = token.removeprefix("Bearer ").strip()
    try:
        body_b64, sig = token.split(".", 1)
        payload = _unb64(body_b64).decode()
        applicant_id, exp_s = payload.rsplit("|", 1)
        exp = int(exp_s)
    except (ValueError, UnicodeDecodeError):
        return None
    expected = hmac.new(_session_secret(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    if (now if now is not None else time.time()) > exp:
        return None
    return applicant_id


def check_service_token(provided: str | None) -> bool:
    """Constant-time comparison of a presented service token against the secret."""
    if not provided:
        return False
    return hmac.compare_digest(provided.strip(), service_token())


def cors_origins() -> list[str]:
    """Allowed browser origins, from env (comma-separated) or dev defaults."""
    raw = os.environ.get("PARIVAHAN_CORS_ORIGINS", "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]


class RateLimiter:
    """Tiny in-process token-bucket limiter keyed by an arbitrary string (e.g. IP).

    Not distributed — one bucket per process. Enough to blunt scraping and
    brute-force on a prototype; a real deployment uses Redis or the edge.
    """

    def __init__(self, capacity: int, refill_per_second: float, now=time.monotonic):
        self.capacity = capacity
        self.refill = refill_per_second
        self._now = now
        self._buckets: dict[str, tuple[float, float]] = {}

    def allow(self, key: str, cost: float = 1.0) -> bool:
        now = self._now()
        tokens, last = self._buckets.get(key, (float(self.capacity), now))
        tokens = min(self.capacity, tokens + (now - last) * self.refill)
        if tokens < cost:
            self._buckets[key] = (tokens, now)
            return False
        self._buckets[key] = (tokens - cost, now)
        return True
