"""Gemini LLM & Voice Provider abstraction for Bol Ke Apply (Module 6).

Targets:
- Gemini Flash Lite (gemini-2.5-flash-lite / gemini-flash-lite-latest) for reasoning
- Gemini Flash TTS for voice synthesis
- Includes a mock fallback for zero-API-key local test environments.
"""

import base64
import json
import logging
import os
from abc import ABC, abstractmethod

from pathlib import Path
import httpx

logger = logging.getLogger("bol_ke_apply_llm")

# Auto-load project root .env
for p in [Path(".env"), Path(__file__).resolve().parents[4] / ".env", Path(__file__).resolve().parents[3] / ".env"]:
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("\"'")
                        if k and not os.environ.get(k):
                            os.environ[k] = v
        except Exception:
            pass
        break


class BaseLLMProvider(ABC):
    """Abstract interface for conversational LLM and voice operations."""

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        """Generate text completion from LLM."""

    @abstractmethod
    def synthesize_speech(self, text: str) -> str | None:
        """Synthesize text into audio and return base64 data URI or None."""

    @abstractmethod
    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe audio into text."""


class MockLLMProvider(BaseLLMProvider):
    """Mock provider for local testing and CI without requiring API keys."""

    def generate_response(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        prompt_lower = prompt.lower()
        if "identity" in prompt_lower or "profile" in prompt_lower:
            return "I can help fetch your verified DigiLocker profile. Please provide your applicant ID."
        if "parking" in prompt_lower or "turn" in prompt_lower or "video" in prompt_lower:
            return "Let me check the Driving Academy video archive for that technique."
        return "Namaste! Welcome to Bol Ke Apply. How can I help with your driving licence today?"

    def synthesize_speech(self, text: str) -> str | None:
        return "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        return "Mera verified profile dikhao"


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini provider interface for Reasoning, TTS, and Transcription."""

    def __init__(
        self,
        api_key: str | None = None,
        chat_model: str | None = None,
        tts_model: str | None = None,
        transcribe_model: str | None = None,
    ):
        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or ""
        )
        self.chat_model = chat_model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.tts_model = tts_model or os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
        self.transcribe_model = transcribe_model or os.getenv("GEMINI_TRANSCRIBE_MODEL", "gemini-2.5-flash")

    def generate_response(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        if not self.api_key:
            return MockLLMProvider().generate_response(prompt, system_instruction)

        # Try gemini-2.5-flash-lite, fallback to gemini-2.5-flash or gemini-flash-latest
        models_to_try = [self.chat_model, "gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-flash-latest"]
        for m in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self.api_key}"
            payload: dict = {
                "contents": [{"parts": [{"text": prompt}]}],
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            try:
                with httpx.Client(timeout=12.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                return parts[0]["text"].strip()
            except Exception as exc:
                logger.warning("Gemini model %s call failed: %s", m, exc)

        return MockLLMProvider().generate_response(prompt, system_instruction)

    def synthesize_speech(self, text: str) -> str | None:
        """Synthesize speech using Gemini TTS if available."""
        if not self.api_key:
            return MockLLMProvider().synthesize_speech(text)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.tts_model}:generateContent?key={self.api_key}"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json={"contents": [{"parts": [{"text": text}]}]})
                if resp.status_code == 200:
                    audio_b64 = resp.json().get("audioContent", "")
                    if audio_b64:
                        return f"data:audio/mp3;base64,{audio_b64}"
        except Exception as exc:
            logger.debug("Gemini TTS fallback to browser speech synthesis: %s", exc)

        return None

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe speech audio using Gemini."""
        if not self.api_key:
            return MockLLMProvider().transcribe_audio(audio_bytes, mime_type)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.transcribe_model}:generateContent?key={self.api_key}"
        b64_data = base64.b64encode(audio_bytes).decode("utf-8")
        payload = {
            "contents": [
                {
                    "parts": [
                        {"inlineData": {"mimeType": mime_type, "data": b64_data}},
                        {"text": "Transcribe this spoken Indian citizen query in Hindi, English or Hinglish exactly. Return ONLY the transcribed text."},
                    ]
                }
            ]
        }
        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
        except Exception as exc:
            logger.warning("Gemini transcription failed: %s", exc)

        return MockLLMProvider().transcribe_audio(audio_bytes, mime_type)


def get_llm_provider(name: str | None = None) -> BaseLLMProvider:
    provider_name = (name or os.getenv("BOL_KE_APPLY_LLM_PROVIDER", "gemini")).lower()
    if provider_name == "mock":
        return MockLLMProvider()
    has_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    if provider_name == "gemini" or has_key:
        return GeminiLLMProvider()
    return MockLLMProvider()
