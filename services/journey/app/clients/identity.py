"""Module 2 → Module 3 client ("what is already verified", AGENTS.md §5.2).

Module 3 is being built in its own silo. Until it merges, the default is a
deterministic stub so Module 2 verifies locally without blocking on it
(§8.6, §11.3). Set IDENTITY_MODE=http and IDENTITY_URL to point at the real
service; the HTTP paths are provisional until Module 3's routes merge.
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime
from typing import Protocol

import httpx
from contracts.identity import Mismatch, MismatchCheckResult, VerifiedProfile


class IdentityClient(Protocol):
    def fetch_identity(self, applicant_id: str) -> VerifiedProfile: ...

    def check_mismatch(self, applicant_id: str) -> MismatchCheckResult: ...


class StubIdentityClient:
    """Deterministic stand-in for Module 3.

    Demo conventions (documented in the repo README):
      - applicant_id ending in "2": GPS RTO and Aadhaar-address RTO disagree —
        the disagreement must be surfaced, never silently resolved (§5.3).
      - applicant_id ending in "9": a name mismatch blocks submission —
        exercises the Rejection-Prevention path.
    """

    def fetch_identity(self, applicant_id: str) -> VerifiedProfile:
        moved = applicant_id.strip().endswith("2")
        return VerifiedProfile(
            applicant_id=applicant_id,
            source="digilocker_aadhaar",
            name="Asha Sharma",
            dob=date(2002, 3, 14),
            address="12 Patel Nagar, New Delhi, 110008",
            photo_url="https://example.invalid/aadhaar-photo.jpg",
            gps_suggested_rto="DL01 (Mall Road)",
            aadhaar_registered_address=(
                "Village Rampur, Sitapur, Uttar Pradesh, 261001"
                if moved
                else "12 Patel Nagar, New Delhi, 110008"
            ),
            addresses_match=not moved,
            fetched_at=datetime.now(UTC),
        )

    def check_mismatch(self, applicant_id: str) -> MismatchCheckResult:
        if applicant_id.strip().endswith("9"):
            return MismatchCheckResult(
                applicant_id=applicant_id,
                mismatches=[
                    Mismatch(
                        field="name",
                        fetched_value="Asha Sharma",
                        issue="Aadhaar name does not match the name on the school-leaving certificate (Asha Kumari Sharma).",
                        suggested_fix="Update the Aadhaar name spelling, or attach the pre-filled name-variation affidavit.",
                    )
                ],
                clear_to_submit=False,
            )
        return MismatchCheckResult(applicant_id=applicant_id, mismatches=[], clear_to_submit=True)


class HttpIdentityClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def fetch_identity(self, applicant_id: str) -> VerifiedProfile:
        res = httpx.get(f"{self.base_url}/identity/{applicant_id}", timeout=10)
        res.raise_for_status()
        return VerifiedProfile.model_validate(res.json())

    def check_mismatch(self, applicant_id: str) -> MismatchCheckResult:
        res = httpx.get(f"{self.base_url}/identity/{applicant_id}/mismatches", timeout=10)
        res.raise_for_status()
        return MismatchCheckResult.model_validate(res.json())


def get_identity_client() -> IdentityClient:
    if os.environ.get("IDENTITY_MODE", "stub").lower() == "http":
        return HttpIdentityClient(os.environ.get("IDENTITY_URL", "http://localhost:8003"))
    return StubIdentityClient()
