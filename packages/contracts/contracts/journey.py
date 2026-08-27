# packages/contracts/journey.py
#
# Module 2 (Journey & Requirements Engine) response shapes.
# JourneyState mirrors the reference JSON in AGENTS.md §7.4 exactly;
# every field beyond that reference is additive (§8.3).

from pydantic import BaseModel

# JourneyStage is defined once, in contracts.enums (AGENTS.md §6 vocabulary).
# Re-exported here so journey consumers can import it alongside the state models.
from contracts.enums import JourneyStage

__all__ = [
    "Certainty",
    "JourneyEvent",
    "JourneyStage",
    "JourneyState",
    "NextAction",
    "RequiredDocument",
]


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
