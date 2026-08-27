"""Identity Contract from AGENTS.md Section 7.1.

Single source of truth for Module 3 (Identity & Document Service).
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class VerifiedProfile(BaseModel):
    applicant_id: str = Field(..., description="Stable identifier for a citizen across all modules")
    source: str = Field(..., description='"digilocker_aadhaar" | "pan" | "manual"')
    name: str
    dob: date
    address: str
    photo_url: str
    gps_suggested_rto: str | None = Field(
        default=None,
        description="Suggested nearest RTO based on GPS/device location (convenience only)",
    )
    aadhaar_registered_address: str | None = Field(
        default=None,
        description="Aadhaar-registered address determining legal RTO jurisdiction",
    )
    addresses_match: bool | None = Field(
        default=None,
        description="True if GPS location matches Aadhaar registered jurisdiction, False otherwise",
    )
    fetched_at: datetime


class Mismatch(BaseModel):
    field: str
    fetched_value: str
    issue: str
    suggested_fix: str


class MismatchCheckResult(BaseModel):
    applicant_id: str
    mismatches: list[Mismatch]
    clear_to_submit: bool
