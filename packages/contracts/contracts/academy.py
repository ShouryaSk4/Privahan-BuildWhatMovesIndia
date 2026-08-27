"""Driving Academy Contract from AGENTS.md Section 7.2.

Single source of truth for Module 4 (Driving Academy Assistant).
"""

from pydantic import BaseModel, Field


class VideoMatchRequest(BaseModel):
    applicant_id: str
    query: str
    journey_stage: str | None = None


class VideoMatchResult(BaseModel):
    video_id: str
    topic: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    fallback_message: str | None = None


class AcademyVideo(BaseModel):
    """Metadata model for a Driving Academy curriculum video clip."""

    video_id: str
    topic: str
    title: str
    description: str
    duration_seconds: int
    video_url: str
    tags: list[str] = Field(default_factory=list)
    hindi_title: str | None = None
    hinglish_keywords: list[str] = Field(default_factory=list)
    thumbnail_url: str | None = None
