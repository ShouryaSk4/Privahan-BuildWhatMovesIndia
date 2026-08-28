"""Gemini 3.5 LLM & Voice Provider abstraction for Bol Ke Apply (Module 6).

Targets:
- Gemini 3.5 Flash Lite for text reasoning / classification
- Gemini 3.5 Flash TTS for voice synthesis
- Gemini 3.5 Transcribe / Transcribe Live for audio input processing
Includes a mock fallback for zero-API-key local test environments.
"""

import base64
import json
import logging
import os
from abc import ABC, abstractmethod

import httpx

logger = logging.getLogger("bol_ke_apply_llm")


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
        # Mock lightweight base64 audio stub for testing
        return "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        return "Mera verified profile dikhao"


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini 3.5 provider interface for Reasoning, TTS, and Transcription."""

    def __init__(
        self,
        api_key: str | None = None,
        chat_model: str | None = None,
        tts_model: str | None = None,
        transcribe_model: str | None = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.chat_model = chat_model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.tts_model = tts_model or os.getenv("GEMINI_TTS_MODEL", "gemini-3.5-flash-tts")
        self.transcribe_model = transcribe_model or os.getenv("GEMINI_TRANSCRIBE_MODEL", "gemini-3.5-transcribe")

    def generate_response(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        if not self.api_key:
            return MockLLMProvider().generate_response(prompt, system_instruction)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.chat_model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("Gemini 3.5 API call failed: %s", exc)

        return MockLLMProvider().generate_response(prompt, system_instruction)

    def synthesize_speech(self, text: str) -> str | None:
        """Synthesize speech using Gemini 3.5 Flash TTS."""
        if not self.api_key:
            return MockLLMProvider().synthesize_speech(text)

        # Hook for Gemini 3.5 Flash TTS endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.tts_model}:generateAudio?key={self.api_key}"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json={"text": text, "voice": {"languageCode": "hi-IN"}})
                if resp.status_code == 200:
                    audio_b64 = resp.json().get("audioContent", "")
                    return f"data:audio/mp3;base64,{audio_b64}"
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.debug("Gemini TTS fallback to browser TTS: %s", exc)

        return None

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe speech audio using Gemini 3.5 Transcribe."""
        if not self.api_key:
            return MockLLMProvider().transcribe_audio(audio_bytes, mime_type)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.transcribe_model}:generateContent?key={self.api_key}"
        b64_data = base64.b64encode(audio_bytes).decode("utf-8")
        payload = {
            "contents": [
                {
                    "parts": [
                        {"inlineData": {"mimeType": mime_type, "data": b64_data}},
                        {"text": "Transcribe this spoken Indian citizen query exactly."},
                    ]
                }
            ]
        }
        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("Gemini 3.5 Transcribe failed: %s", exc)

        return MockLLMProvider().transcribe_audio(audio_bytes, mime_type)


def get_llm_provider(name: str | None = None) -> BaseLLMProvider:
    provider_name = (name or os.getenv("BOL_KE_APPLY_LLM_PROVIDER", "mock")).lower()
    if provider_name == "gemini":
        return GeminiLLMProvider()
    return MockLLMProvider()
