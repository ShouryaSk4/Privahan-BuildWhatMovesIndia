"""Module 2 → Module 3 client ("what is already verified", AGENTS.md §5.2).

Module 3 is merged, so the default is `IDENTITY_MODE=http` against the real
Identity Service. The stub remains for offline development and tests (§8.6,
§11.3) and mirrors Module 3's three demo personas so both paths behave alike.

Module 3's real routes (services/identity):
    GET /identity/fetch/{applicant_id}?gps_suggested_rto=...
    GET /identity/mismatch-check/{applicant_id}
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime
from typing import Protocol

import httpx
from contracts.enums import IdentitySource
from contracts.identity import Mismatch, MismatchCheckResult, VerifiedProfile

# Module 2 asks for a convenient nearby RTO; Module 3 decides jurisdiction from
# the Aadhaar-registered address. The two are never conflated (§5.3).
DEFAULT_GPS_SUGGESTED_RTO = os.environ.get("JOURNEY_GPS_RTO", "KA-03 Indiranagar")


class IdentityUnavailable(Exception):
    """Module 3 could not be reached or returned an error."""


class IdentityClient(Protocol):
    def fetch_identity(self, applicant_id: str) -> VerifiedProfile: ...

    def check_mismatch(self, applicant_id: str) -> MismatchCheckResult: ...


class StubIdentityClient:
    """Offline stand-in for Module 3, mirroring its mock e-KYC personas.

      - "applicant_student"  → Aadhaar jurisdiction (Lucknow) disagrees with the
        device location (Bengaluru). Advisory, surfaced for an explicit choice.
      - "applicant_mismatch" → Aadhaar vs PAN name mismatch. Blocks submission.
      - anything else        → clean profile, clear to submit.
    """

    def fetch_identity(self, applicant_id: str) -> VerifiedProfile:
        student = applicant_id.strip() == "applicant_student"
        mismatch = applicant_id.strip() == "applicant_mismatch"
        if student:
            name, dob = "Priya Sharma", date(2004, 2, 10)
            address = "Room 102, Kaveri Hostel, Electronic City, Bengaluru, KA - 560100"
            aadhaar_address = "House 12, Gomti Nagar, Lucknow, UP - 226010"
        elif mismatch:
            name, dob = "Vikram Singh Chauhan", date(2001, 11, 20)
            address = aadhaar_address = "Sector 15, Rohini, Delhi, DL - 110089"
        else:
            name, dob = "Rohan Verma", date(2003, 8, 15)
            address = aadhaar_address = "Flat 204, Palm Grove, Whitefield, Bengaluru, KA - 560066"

        return VerifiedProfile(
            applicant_id=applicant_id,
            source=IdentitySource.DIGILOCKER_AADHAAR,
            name=name,
            dob=dob,
            address=address,
            photo_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=300",
            gps_suggested_rto=DEFAULT_GPS_SUGGESTED_RTO,
            aadhaar_registered_address=aadhaar_address,
            addresses_match=not student,
            fetched_at=datetime.now(UTC),
        )

    def check_mismatch(self, applicant_id: str) -> MismatchCheckResult:
        mismatches: list[Mismatch] = []
        if applicant_id.strip() == "applicant_mismatch":
            mismatches.append(
                Mismatch(
                    field="name",
                    fetched_value="Vikram Singh Chauhan",
                    issue="Aadhaar name 'Vikram Singh Chauhan' differs from PAN record 'Vikram S Chauhan'.",
                    suggested_fix="Ensure full name matches government identity databases or upload gazette notification.",
                )
            )
        if applicant_id.strip() == "applicant_student":
            mismatches.append(
                Mismatch(
                    field="aadhaar_registered_address",
                    fetched_value="House 12, Gomti Nagar, Lucknow, UP - 226010",
                    issue="Your current device location suggests a different RTO than your Aadhaar jurisdiction.",
                    suggested_fix="You can apply at your Aadhaar jurisdiction RTO, or update your Aadhaar address with current local residence proof.",
                )
            )
        return MismatchCheckResult(
            applicant_id=applicant_id,
            mismatches=mismatches,
            clear_to_submit=len(mismatches) == 0,
        )


class DirectIdentityClient:
    """Calls identity_service directly without loopback HTTP calls."""

    def fetch_identity(self, applicant_id: str) -> VerifiedProfile:
        from identity_service.main import service
        return service.fetch_identity(
            applicant_id=applicant_id,
            gps_suggested_rto=DEFAULT_GPS_SUGGESTED_RTO,
        )

    def check_mismatch(self, applicant_id: str) -> MismatchCheckResult:
        from identity_service.main import service
        return service.check_mismatch(applicant_id=applicant_id)


class HttpIdentityClient:
    """Talks to the real Module 3 service."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str, **params) -> dict:
        try:
            res = httpx.get(
                f"{self.base_url}{path}",
                params=params or None,
                timeout=10,
                follow_redirects=True,
            )
        except httpx.HTTPError as exc:
            raise IdentityUnavailable(
                f"Identity Service unreachable at {self.base_url}: {exc}"
            ) from exc
        if res.status_code >= 400:
            raise IdentityUnavailable(
                f"Identity Service returned {res.status_code}: {res.text[:200]}"
            )
        return res.json()

    def fetch_identity(self, applicant_id: str) -> VerifiedProfile:
        return VerifiedProfile.model_validate(
            self._get(
                f"/identity/fetch/{applicant_id}",
                gps_suggested_rto=DEFAULT_GPS_SUGGESTED_RTO,
            )
        )

    def check_mismatch(self, applicant_id: str) -> MismatchCheckResult:
        return MismatchCheckResult.model_validate(
            self._get(f"/identity/mismatch-check/{applicant_id}")
        )


def get_identity_client() -> IdentityClient:
    """Module 3 client factory. Direct in serverless, HTTP in multi-process."""
    mode = os.environ.get("IDENTITY_MODE", "").lower()
    if mode == "stub":
        return StubIdentityClient()
    if mode == "direct":
        return DirectIdentityClient()
    # In Vercel serverless / combined runtime, Direct in-memory invocation is 100% reliable
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_URL"):
        try:
            return DirectIdentityClient()
        except ImportError:
            pass
    return HttpIdentityClient(os.environ.get("IDENTITY_URL", "http://localhost:8003"))
