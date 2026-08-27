"""MCP Tool Contract declarations from AGENTS.md Section 7.3.

Module 6 wraps these contracts as MCP tools for the current merge:
- tool "fetch_identity"(applicant_id: str) -> VerifiedProfile
- tool "check_mismatch"(applicant_id: str) -> MismatchCheckResult
- tool "match_video"(request: VideoMatchRequest) -> VideoMatchResult

Module 2 now exists (merged 28 Aug 2026), so the journey-state tools that
AGENTS.md §2 held back are unblocked. Module 6 may now add:
- tool "whats_next"(applicant_id: str) -> JourneyState
- tool "start_application"(applicant_id: str) -> JourneyState
- tool "report_event"(event: JourneyEvent) -> JourneyState

These mirror Module 2's HTTP interface 1:1 (services/journey):
    GET  /journey/{applicant_id}
    POST /journey/{applicant_id}/apply
    POST /journey/{applicant_id}/events
Module 6 owns the wrapping; this file only declares the contract.
"""

from pydantic import BaseModel

from contracts.academy import VideoMatchRequest, VideoMatchResult
from contracts.identity import MismatchCheckResult, VerifiedProfile
from contracts.journey import JourneyEvent, JourneyState


class FetchIdentityToolInput(BaseModel):
    applicant_id: str


class CheckMismatchToolInput(BaseModel):
    applicant_id: str


class MatchVideoToolInput(VideoMatchRequest):
    pass


class WhatsNextToolInput(BaseModel):
    applicant_id: str


class StartApplicationToolInput(BaseModel):
    applicant_id: str
    confirmed_rto_code: str | None = None


class ReportEventToolInput(JourneyEvent):
    pass


__all__ = [
    "CheckMismatchToolInput",
    "FetchIdentityToolInput",
    "JourneyEvent",
    "JourneyState",
    "MatchVideoToolInput",
    "MismatchCheckResult",
    "ReportEventToolInput",
    "StartApplicationToolInput",
    "VerifiedProfile",
    "VideoMatchRequest",
    "VideoMatchResult",
    "WhatsNextToolInput",
]
