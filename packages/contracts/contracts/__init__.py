"""Parivahan MVP Shared Contracts.

Single Source of Truth across all modules and services.
"""

from contracts.academy import AcademyVideo, VideoMatchRequest, VideoMatchResult
from contracts.enums import IdentitySource, JourneyStage
from contracts.gateway import (
    GovApplicationStatus,
    GovSubmissionResult,
    LLApplicationSubmission,
    SlotBookingRequest,
    SlotBookingResult,
    TestResultReport,
    TestSlot,
)
from contracts.identity import Mismatch, MismatchCheckResult, VerifiedProfile
from contracts.journey import (
    Certainty,
    JourneyEvent,
    JourneyState,
    NextAction,
    RequiredDocument,
)
from contracts.mcp_tools import (
    CheckMismatchToolInput,
    FetchIdentityToolInput,
    MatchVideoToolInput,
)

__all__ = [
    "AcademyVideo",
    "Certainty",
    "CheckMismatchToolInput",
    "FetchIdentityToolInput",
    "GovApplicationStatus",
    "GovSubmissionResult",
    "IdentitySource",
    "JourneyEvent",
    "JourneyStage",
    "JourneyState",
    "LLApplicationSubmission",
    "MatchVideoToolInput",
    "Mismatch",
    "MismatchCheckResult",
    "NextAction",
    "RequiredDocument",
    "SlotBookingRequest",
    "SlotBookingResult",
    "TestResultReport",
    "TestSlot",
    "VerifiedProfile",
    "VideoMatchRequest",
    "VideoMatchResult",
]
