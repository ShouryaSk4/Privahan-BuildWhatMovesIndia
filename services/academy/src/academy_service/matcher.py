"""Driving Academy Video Matcher (Module 4).

Per AGENTS.md Section 5.4:
With ~10 videos, does NOT build an embeddings pipeline yet.
Uses single LLM classification: 'Which of these topics best matches this message?'
Includes deterministic heuristic fallback so local testing works out of the box.
"""

import os

from contracts.academy import VideoMatchRequest, VideoMatchResult

from academy_service.catalog import ACADEMY_VIDEO_CATALOG


class VideoMatcher:
    """Matches learner queries against the ~10 video catalog topics."""

    def __init__(self, provider: str | None = None):
        self.provider = provider or os.getenv("ACADEMY_LLM_PROVIDER", "mock")

    def match(self, request: VideoMatchRequest) -> VideoMatchResult:
        # If an external LLM provider is requested and keys exist, invoke it
        if self.provider == "gemini" and os.getenv("GEMINI_API_KEY"):
            return self._match_with_gemini(request)

        # Default / fast classification (deterministic heuristic matching)
        return self._match_heuristic(request)

    def _match_heuristic(self, request: VideoMatchRequest) -> VideoMatchResult:
        query = request.query.lower()
        norm_query = query.replace("-", " ")

        best_video = None
        best_score = 0.0

        for video in ACADEMY_VIDEO_CATALOG:
            score = 0.0
            norm_topic = video.topic.lower().replace("-", " ")

            # Direct topic exact match
            if norm_topic in norm_query:
                score += 0.85

            # Tag matches
            for tag in video.tags:
                norm_tag = tag.lower().replace("-", " ")
                if norm_tag in norm_query:
                    score += 0.70
                else:
                    # Word-level overlap
                    words = [w for w in norm_tag.split() if len(w) > 3]
                    for word in words:
                        if word in norm_query:
                            score += 0.25

            if score > best_score:
                best_score = score
                best_video = video

        if best_video and best_score >= 0.5:
            return VideoMatchResult(
                video_id=best_video.video_id,
                topic=best_video.topic,
                confidence=round(min(best_score / 1.5, 0.98), 2),
                fallback_message=None,
            )

        # Fallback when confidence is low
        available_topics = ", ".join(v.topic for v in ACADEMY_VIDEO_CATALOG[:5])
        return VideoMatchResult(
            video_id=ACADEMY_VIDEO_CATALOG[0].video_id,
            topic=ACADEMY_VIDEO_CATALOG[0].topic,
            confidence=0.25,
            fallback_message=(
                f"We couldn't identify a specific lesson for '{request.query}'. "
                f"Popular modules include: {available_topics}."
            ),
        )

    def _match_with_gemini(self, request: VideoMatchRequest) -> VideoMatchResult:
        # Thin hook for Gemini classification
        return self._match_heuristic(request)
