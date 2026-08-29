"""Driving Academy Video Matcher (Module 4).

Per AGENTS.md Section 5.4:
Uses single LLM classification (Gemini Flash Lite / 1.5 Flash / 2.0 Flash)
to match user queries (English, Hindi, Hinglish) to one of ~10 video topics.
Includes an intelligent multilingual heuristic fallback for offline / test environments.
"""

import json
import logging
import os

import httpx
from contracts.academy import VideoMatchRequest, VideoMatchResult

from academy_service.catalog import ACADEMY_VIDEO_CATALOG, get_video_by_topic

logger = logging.getLogger("academy_matcher")

TOPIC_LIST = [video.topic for video in ACADEMY_VIDEO_CATALOG]


class VideoMatcher:
    """Matches learner queries against the ~10 video catalog topics."""

    def __init__(self, provider: str | None = None, model: str | None = None):
        self.provider = provider or os.getenv("ACADEMY_LLM_PROVIDER", "mock").lower()
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.api_key = os.getenv("GEMINI_API_KEY", "")

    def match(self, request: VideoMatchRequest) -> VideoMatchResult:
        # If Gemini is configured and API key is present, use LLM classification
        if (self.provider == "gemini" or self.api_key) and self.api_key:
            try:
                llm_result = self._match_with_gemini(request)
                if llm_result:
                    return llm_result
            except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as exc:
                logger.warning("Gemini classification failed, falling back to heuristic: %s", exc)

        # Fallback to local multilingual heuristic classification
        return self._match_heuristic(request)

    def _match_with_gemini(self, request: VideoMatchRequest) -> VideoMatchResult | None:
        """Call Google Gemini API for zero-shot query classification."""
        topics_str = "\n".join(f"- {t}" for t in TOPIC_LIST)
        prompt = f"""You are the Parivahan Driving Academy matching engine.
Learner message (can be English, Hindi, or Hinglish): "{request.query}"

Classify this query into exactly ONE of the following 10 driving lesson topics:
{topics_str}

Respond strictly in valid JSON with no markdown wrapping:
{{
  "topic": "<one of the exact 10 topics above>",
  "confidence": <float between 0.0 and 1.0>,
  "explanation": "<brief reason>"
}}
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
        }

        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                chosen_topic = parsed.get("topic", "").strip().lower()
                confidence = float(parsed.get("confidence", 0.8))

                matched_video = get_video_by_topic(chosen_topic)
                if matched_video:
                    return VideoMatchResult(
                        video_id=matched_video.video_id,
                        topic=matched_video.topic,
                        confidence=round(min(confidence, 0.99), 2),
                        fallback_message=None if confidence >= 0.4 else "Topic matched with low confidence.",
                        video_url=matched_video.video_url,
                        title=matched_video.title,
                        description=matched_video.description,
                    )
        return None

    def _match_heuristic(self, request: VideoMatchRequest) -> VideoMatchResult:
        """Deterministic multilingual heuristic matcher supporting English, Hindi & Hinglish."""
        query = request.query.strip().lower()
        norm_query = query.replace("-", " ")

        best_video = None
        best_score = 0.0

        for video in ACADEMY_VIDEO_CATALOG:
            score = 0.0
            norm_topic = video.topic.lower().replace("-", " ")

            # 1. Exact topic match
            if norm_topic in norm_query:
                score += 0.85

            # 2. Hindi title match
            if video.hindi_title and any(word in norm_query for word in video.hindi_title.split()):
                score += 0.80

            # 3. Hinglish keywords match
            for hk in video.hinglish_keywords:
                norm_hk = hk.lower().replace("-", " ")
                if norm_hk in norm_query:
                    score += 0.90
                else:
                    # Partial Hinglish phrase match
                    words = [w for w in norm_hk.split() if len(w) > 3]
                    for w in words:
                        if w in norm_query:
                            score += 0.35

            # 4. Tags match (English + Hindi tags)
            for tag in video.tags:
                norm_tag = tag.lower().replace("-", " ")
                if norm_tag in norm_query:
                    score += 0.70
                else:
                    words = [w for w in norm_tag.split() if len(w) > 3]
                    for w in words:
                        if w in norm_query:
                            score += 0.25

            if score > best_score:
                best_score = score
                best_video = video

        if best_video and best_score >= 0.45:
            return VideoMatchResult(
                video_id=best_video.video_id,
                topic=best_video.topic,
                confidence=round(min(best_score / 1.5, 0.98), 2),
                fallback_message=None,
                video_url=best_video.video_url,
                title=best_video.title,
                description=best_video.description,
            )

        # Fallback when confidence is low
        available_topics = ", ".join(v.topic for v in ACADEMY_VIDEO_CATALOG[:5])
        return VideoMatchResult(
            video_id=ACADEMY_VIDEO_CATALOG[0].video_id,
            topic=ACADEMY_VIDEO_CATALOG[0].topic,
            confidence=0.20,
            fallback_message=(
                f"We couldn't identify a specific lesson for '{request.query}'. "
                f"Popular modules include: {available_topics}."
            ),
            video_url=ACADEMY_VIDEO_CATALOG[0].video_url,
            title=ACADEMY_VIDEO_CATALOG[0].title,
            description=ACADEMY_VIDEO_CATALOG[0].description,
        )
