"""Auth + rate-limit dependencies for Module 2's citizen-facing API.

A session token (minted by POST /session) binds a browser to exactly one
applicant_id. Every /journey/{applicant_id}/* route requires that token AND
that its bound applicant_id matches the path — so knowing or guessing another
citizen's id gets you nothing (closes the IDOR).
"""

from __future__ import annotations

from contracts.security import RateLimiter, verify_session
from fastapi import Header, HTTPException, Request

# Per-IP limits (in-process; a real deployment uses Redis/edge).
_session_limiter = RateLimiter(capacity=20, refill_per_second=0.5)  # ~mint bursts
_api_limiter = RateLimiter(capacity=120, refill_per_second=4.0)  # general API


def _client_key(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_api(request: Request) -> None:
    if not _api_limiter.allow(_client_key(request)):
        raise HTTPException(status_code=429, detail="Too many requests — slow down.")


def rate_limit_session(request: Request) -> None:
    if not _session_limiter.allow(_client_key(request)):
        raise HTTPException(status_code=429, detail="Too many session requests — try again shortly.")


def require_owner(
    applicant_id: str,
    authorization: str | None = Header(default=None),
) -> str:
    """Verify the bearer session token and that it owns this applicant_id."""
    bound = verify_session(authorization)
    if bound is None:
        raise HTTPException(status_code=401, detail="Valid session token required.")
    if bound != applicant_id:
        raise HTTPException(status_code=403, detail="This session does not own that application.")
    return applicant_id
