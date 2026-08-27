"""MCP Tool Contract declarations from AGENTS.md Section 7.3.

Module 6 wraps these contracts as MCP tools for the current merge:
- tool "fetch_identity"(applicant_id: str) -> VerifiedProfile
- tool "check_mismatch"(applicant_id: str) -> MismatchCheckResult
- tool "match_video"(request: VideoMatchRequest) -> VideoMatchResult

Nothing else is exposed until Module 2 exists.
"""

from pydantic import BaseModel

from contracts.academy import VideoMatchRequest, VideoMatchResult
from contracts.identity import MismatchCheckResult, VerifiedProfile


class FetchIdentityToolInput(BaseModel):
    applicant_id: str


class CheckMismatchToolInput(BaseModel):
    applicant_id: str


class MatchVideoToolInput(VideoMatchRequest):
    pass


__all__ = [
    "CheckMismatchToolInput",
    "FetchIdentityToolInput",
    "MatchVideoToolInput",
    "MismatchCheckResult",
    "VerifiedProfile",
    "VideoMatchRequest",
    "VideoMatchResult",
]
