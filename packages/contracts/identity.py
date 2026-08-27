# packages/contracts/identity.py

from datetime import date, datetime

from pydantic import BaseModel


class VerifiedProfile(BaseModel):
    applicant_id: str
    source: str  # "digilocker_aadhaar" | "pan" | "manual"
    name: str
    dob: date
    address: str
    photo_url: str
    gps_suggested_rto: str | None = None
    aadhaar_registered_address: str | None = None
    addresses_match: bool | None = None
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
