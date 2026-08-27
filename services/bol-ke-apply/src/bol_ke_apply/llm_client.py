"""Thin LLM Provider abstraction for Bol Ke Apply (Module 6).

Per AGENTS.md Section 4.4:
Allows switching between Gemini, OpenAI, or a Mock conversational driver
without rewriting Module 6 tool wrappers or routing.
"""

import os
from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract interface for conversational LLM provider."""

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        pass


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


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini provider interface."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def generate_response(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        if not self.api_key:
            # Fallback to mock when key is missing
            return MockLLMProvider().generate_response(prompt, system_instruction)
        # Production hook for google-genai
        return f"[Gemini]: Response to: {prompt[:50]}..."


def get_llm_provider(name: str | None = None) -> BaseLLMProvider:
    provider_name = (name or os.getenv("BOL_KE_APPLY_LLM_PROVIDER", "mock")).lower()
    if provider_name == "gemini":
        return GeminiLLMProvider()
    return MockLLMProvider()
