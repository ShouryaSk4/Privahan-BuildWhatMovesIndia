# packages/contracts/gateway.py
#
# Module 5 (Integration Gateway) — the stable internal interface the rest of
# the platform codes against. Module 5 is the ONLY module that talks to
# Sarathi / Vahan / eChallan (AGENTS.md §5.5); everyone else speaks these
# shapes to Module 5 and never sees a government payload.

from datetime import datetime

from pydantic import BaseModel


class LLApplicationSubmission(BaseModel):
    applicant_id: str
    name: str
    dob: str  # ISO date string as verified by Module 3
    address: str
    photo_url: str
    rto_code: str
    vehicle_class: str = "LMV"  # first-time car licence journey


class GovSubmissionResult(BaseModel):
    application_number: str
    status: str  # "received"
    submitted_at: datetime


class GovApplicationStatus(BaseModel):
    application_number: str
    applicant_id: str
    stage: str  # gateway-normalized government-side status
    updated_at: datetime
    failed_checkpoint: str | None = None  # additive: set when stage == "dl_test_failed"
    integrity_tier: str | None = None  # additive: proctoring outcome of the last online test


class TestSlot(BaseModel):
    slot_id: str
    rto_code: str
    starts_at: datetime
    capacity_left: int


class SlotBookingRequest(BaseModel):
    applicant_id: str
    application_number: str
    slot_id: str


class SlotBookingResult(BaseModel):
    booking_id: str
    slot: TestSlot
    confirmed: bool


class TestResultReport(BaseModel):
    application_number: str
    test_type: str  # "ll" | "dl"
    passed: bool
    failed_checkpoint: str | None = None
    # Additive: proctoring integrity (tiered human-review model — never auto-fail)
    integrity_score: int | None = None
    integrity_tier: str | None = None  # "clear" | "review" | "flagged"
    integrity_events: int | None = None
