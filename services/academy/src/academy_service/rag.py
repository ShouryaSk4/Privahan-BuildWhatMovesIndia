"""RTO Complete Driving Manual RAG Engine (Module 4).

Provides Retrieval-Augmented Generation over the 100,000-character
'RTO Complete Driving Competency & Test Manual' using semantic chunking,
BM25/TF-IDF similarity search, and Gemini 2.5 Flash Lite synthesis.
"""

import json
import logging
import math
import os
import re
from pathlib import Path
from typing import Any

import httpx
from contracts.academy import AcademyAskRequest, AcademyAskResponse, VideoMatchRequest

from academy_service.matcher import VideoMatcher

logger = logging.getLogger("academy_rag")

DATA_DIR = Path(__file__).parent / "data"
CHUNKS_FILE = DATA_DIR / "rto_manual_chunks.json"


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words."""
    return re.findall(r"\b[a-z0-9]{2,}\b", text.lower())


class ManualRAGEngine:
    """RAG engine over the official RTO Complete Driving Manual."""

    def __init__(self, matcher: VideoMatcher | None = None):
        self.matcher = matcher or VideoMatcher()
        self.chunks: list[dict[str, Any]] = []
        self.chunk_tokens: list[list[str]] = []
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self._load_manual()

    def _load_manual(self) -> None:
        """Load and index manual chunks."""
        if CHUNKS_FILE.exists():
            try:
                with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                self.chunk_tokens = [_tokenize(c["title"] + " " + c["content"]) for c in self.chunks]
                logger.info("Loaded %d manual chunks from %s", len(self.chunks), CHUNKS_FILE)
            except Exception as e:
                logger.error("Failed to load manual chunks: %s", e)
        else:
            logger.warning("RTO manual chunks file not found at %s", CHUNKS_FILE)

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Retrieve the top_k most relevant chunks using BM25-style term weighting."""
        if not self.chunks:
            return []

        q_tokens = _tokenize(query)
        if not q_tokens:
            return self.chunks[:top_k]

        scores = []
        n_chunks = len(self.chunks)

        for i, doc_tokens in enumerate(self.chunk_tokens):
            score = 0.0
            doc_len = len(doc_tokens)
            doc_set = set(doc_tokens)
            for qt in q_tokens:
                if qt in doc_set:
                    # Term frequency
                    tf = doc_tokens.count(qt)
                    # IDF estimate
                    df = sum(1 for tokens in self.chunk_tokens if qt in tokens)
                    idf = math.log((n_chunks - df + 0.5) / (df + 0.5) + 1.0)
                    score += idf * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * (doc_len / 200.0)))
            scores.append((score, i))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_indices = [idx for sc, idx in scores[:top_k] if sc > 0]
        if not top_indices:
            top_indices = [scores[0][1]] if scores else [0]

        return [self.chunks[i] for i in top_indices]

    def ask(self, request: AcademyAskRequest) -> AcademyAskResponse:
        """Answer candidate question using retrieved manual context and Gemini."""
        query = request.query.strip()
        retrieved_chunks = self.retrieve(query, top_k=3)
        source_titles = [c["title"] for c in retrieved_chunks]

        # Check if query matches a driving test video
        matched_video = None
        try:
            match_res = self.matcher.match(
                VideoMatchRequest(
                    applicant_id=request.applicant_id,
                    query=query,
                    journey_stage=request.journey_stage,
                )
            )
            if match_res and match_res.confidence >= 0.45:
                matched_video = match_res
        except Exception as e:
            logger.warning("Video match check failed during RAG: %s", e)

        # Generate answer via Gemini if API key is present
        if self.api_key:
            try:
                gemini_answer = self._synthesize_with_gemini(query, retrieved_chunks)
                if gemini_answer:
                    return AcademyAskResponse(
                        query=query,
                        answer=gemini_answer,
                        source_sections=source_titles,
                        matched_video=matched_video,
                    )
            except Exception as exc:
                logger.warning("Gemini RAG synthesis failed, using local excerpt: %s", exc)

        # Fallback local synthesis
        local_answer = self._format_local_answer(query, retrieved_chunks)
        return AcademyAskResponse(
            query=query,
            answer=local_answer,
            source_sections=source_titles,
            matched_video=matched_video,
        )

    def _synthesize_with_gemini(self, query: str, context_chunks: list[dict[str, Any]]) -> str | None:
        """Synthesize authoritative response using Gemini 2.5 Flash Lite."""
        context_text = "\n\n---\n\n".join(
            f"### SECTION: {c['title']}\n{c['content']}" for c in context_chunks
        )

        prompt = f"""You are the Parivahan Driving Safety Officer and AI Driving Academy Coach.
Answer the candidate's question accurately, concisely, and authoritatively based STRICTLY on the attached excerpts from the official 'RTO Complete Driving Competency & Test Manual' (Motor Vehicles Act 1988 & Central Motor Vehicles Rules 1989).

INSTRUCTIONS:
1. Provide actionable, practical driving guidance or statutory rules.
2. If discussing a driving test maneuver (8-track, hill start, reverse park), mention exact techniques like clutch bite point, mirror checks, steering hand posture, and test sensor checkpoints.
3. Be clear, polite, encouraging, and cite the relevant manual section.
4. Keep the response formatted in clean markdown bullet points (maximum 150 words).

OFFICIAL RTO MANUAL EXCERPTS:
{context_text}

CANDIDATE QUESTION:
{query}
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 400},
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return None

    def _format_local_answer(self, query: str, context_chunks: list[dict[str, Any]]) -> str:
        """Synthesize local excerpt when LLM is offline."""
        if not context_chunks:
            return "According to the RTO Driving Manual, always maintain safe vehicle control, wear your seatbelt, and adhere to speed limits."

        primary = context_chunks[0]
        # Extract first 2-3 sentences or paragraphs
        lines = [line for line in primary["content"].split("\n") if len(line) > 30][:3]
        summary = " ".join(lines)
        return (
            f"**From RTO Manual — {primary['title']}:**\n\n"
            f"{summary}\n\n"
            f"*(Reference: Motor Vehicles Act 1988 & CMVR 1989 Guidelines)*"
        )
