# packages/contracts/journey.py
#
# Module 2 (Journey & Requirements Engine) response shapes.
# JourneyState mirrors the reference JSON in AGENTS.md §7.4 exactly;
# every field beyond that reference is additive (§8.3).

from enum import Enum

from pydantic import BaseModel


class JourneyStage(str, Enum):
    # Shared vocabulary — AGENTS.md §6. Do not create local synonyms.
    no_licence = "no_licence"
    ll_application_submitted = "ll_application_submitted"
    ll_documents_verified = "ll_documents_verified"
    ll_test_scheduled = "ll_test_scheduled"
    ll_issued = "ll_issued"
    practice_window = "practice_window"
    dl_test_booked = "dl_test_booked"
    dl_test_result_fail = "dl_test_result_fail"
    dl_test_result_pass = "dl_test_result_pass"
    dl_issued = "dl_issued"


class NextAction(BaseModel):
    type: str
    label: str


class Certainty(BaseModel):
    cost_inr: int
    eta_days: int
    visit_count: int


class RequiredDocument(BaseModel):
    code: str
    label: str
    satisfied_by_ekyc: bool = False


class JourneyState(BaseModel):
    applicant_id: str
    journey_type: str = "first_time_licence"
    current_stage: JourneyStage
    next_action: NextAction
    certainty: Certainty
    # Additive beyond §7.4:
    required_documents: list[RequiredDocument] = []
    stage_detail: str | None = None
    application_number: str | None = None


class JourneyEvent(BaseModel):
    # An observed fact reported to Module 2 that may advance the state machine.
    applicant_id: str
    event: str  # e.g. "ll_application_submitted", "ll_test_passed", "dl_test_failed"
