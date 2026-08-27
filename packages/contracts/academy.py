# packages/contracts/academy.py

from pydantic import BaseModel


class VideoMatchRequest(BaseModel):
    applicant_id: str
    query: str
    journey_stage: str | None = None


class VideoMatchResult(BaseModel):
    video_id: str
    topic: str
    confidence: float
    fallback_message: str | None = None
