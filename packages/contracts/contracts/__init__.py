"""Parivahan MVP Shared Contracts.

Single Source of Truth across all modules and services.
"""

from contracts.academy import AcademyVideo, VideoMatchRequest, VideoMatchResult
from contracts.enums import IdentitySource, JourneyStage
from contracts.identity import Mismatch, MismatchCheckResult, VerifiedProfile
from contracts.mcp_tools import (
    CheckMismatchToolInput,
    FetchIdentityToolInput,
    MatchVideoToolInput,
)

__all__ = [
    "AcademyVideo",
    "CheckMismatchToolInput",
    "FetchIdentityToolInput",
    "IdentitySource",
    "JourneyStage",
    "MatchVideoToolInput",
    "Mismatch",
    "MismatchCheckResult",
    "VerifiedProfile",
    "VideoMatchRequest",
    "VideoMatchResult",
]
