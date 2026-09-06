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


def _pcm_to_wav_data_uri(b64_pcm: str, mime: str) -> str | None:
    """Wrap Gemini's raw PCM (audio/L16;rate=NNNNN) in a WAV header so a browser
    <audio> element can play it from a data URI."""
    import re
    import struct

    try:
        pcm = base64.b64decode(b64_pcm)
    except (ValueError, TypeError):
        return None
    if not pcm:
        return None
    m = re.search(r"rate=(\d+)", mime or "")
    rate = int(m.group(1)) if m else 24000
    channels, bits = 1, 16
    byte_rate = rate * channels * bits // 8
    block_align = channels * bits // 8
    header = (
        b"RIFF"
        + struct.pack("<I", 36 + len(pcm))
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, channels, rate, byte_rate, block_align, bits)
        + b"data"
        + struct.pack("<I", len(pcm))
    )
    return "data:audio/wav;base64," + base64.b64encode(header + pcm).decode("ascii")


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

    # Optional capabilities — providers that can't do these inherit the defaults,
    # and callers fall back gracefully.

    def chat_with_tools(self, messages: list[dict], tools: list[dict]) -> dict | None:
        """One model turn with native function calling.

        Returns the raw assistant message ({"content": ..., "tool_calls": [...]})
        or None when the provider does not support tool calling / has no key —
        the agent then falls back to keyword routing.
        """
        return None

    def moderate(self, text: str) -> bool:
        """True if the text should be refused. Default: never flag."""
        return False


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
        self.chat_model = chat_model or os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
        self.tts_model = tts_model or os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
        self.tts_voice = os.getenv("GEMINI_TTS_VOICE", "Kore")
        self.transcribe_model = transcribe_model or os.getenv("GEMINI_TRANSCRIBE_MODEL", "gemini-3.5-transcribe")

    def generate_response(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        # Try distinct models in order
        candidates = [self.chat_model, "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]
        seen = set()
        models_to_try = [m for m in candidates if m and not (m in seen or seen.add(m))]

        for m in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
            headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
            payload: dict = {
                "contents": [{"parts": [{"text": prompt}]}],
            }
            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            try:
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        cand_list = data.get("candidates", [])
                        if cand_list:
                            parts = cand_list[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                return parts[0]["text"].strip()
                    else:
                        logger.debug("Gemini %s response %s: %s", m, resp.status_code, resp.text[:120])
            except Exception as exc:
                logger.warning("Gemini model %s call failed: %s", m, exc)

        return MockLLMProvider().generate_response(prompt, system_instruction)

    def chat_with_tools(self, messages: list[dict], tools: list[dict]) -> dict | None:
        """Execute multi-turn conversational tool calling using Gemini 3.7 Flash."""
        if not self.api_key:
            return None

        # Build contents array
        contents = []
        system_text = ""
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content") or ""
            if role == "system":
                system_text += content + "\n"
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                parts = []
                if content:
                    parts.append({"text": content})
                for call in m.get("tool_calls") or []:
                    fn = call.get("function", {})
                    try:
                        args = json.loads(fn.get("arguments") or "{}")
                    except Exception:
                        args = {}
                    parts.append({"functionCall": {"name": fn.get("name", ""), "args": args}})
                if parts:
                    contents.append({"role": "model", "parts": parts})
            elif role == "tool":
                tool_name = m.get("tool_call_id") or "tool"
                contents.append({
                    "role": "user",
                    "parts": [{"text": f"Tool '{tool_name}' returned: {content}"}]
                })

        # Build function declarations
        function_declarations = []
        for t in tools:
            fn = t.get("function", {})
            function_declarations.append({
                "name": fn.get("name", ""),
                "description": fn.get("description", ""),
                "parameters": fn.get("parameters", {}),
            })

        payload: dict = {"contents": contents}
        # Gemini rejects an empty functionDeclarations list; an empty tools
        # argument means "reply in prose now" (the final summarise turn).
        if function_declarations:
            payload["tools"] = [{"functionDeclarations": function_declarations}]
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text.strip()}]}

        candidates = [self.chat_model, "gemini-3.7-flash", "gemini-3.6-flash"]
        for m in candidates:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
            headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
            try:
                with httpx.Client(timeout=12.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        cand = data.get("candidates", [{}])[0]
                        parts = cand.get("content", {}).get("parts", [])
                        
                        tool_calls = []
                        text_parts = []
                        for idx, p in enumerate(parts):
                            if "functionCall" in p:
                                fc = p["functionCall"]
                                tool_calls.append({
                                    "id": f"call_{idx}_{fc.get('name')}",
                                    "type": "function",
                                    "function": {
                                        "name": fc.get("name"),
                                        "arguments": json.dumps(fc.get("args", {})),
                                    },
                                })
                            elif "text" in p:
                                text_parts.append(p["text"])

                        reply_text = "\n".join(text_parts).strip()
                        return {
                            "content": reply_text if reply_text else None,
                            "tool_calls": tool_calls,
                        }
                    else:
                        logger.warning("Gemini %s tool calling error (%s): %s", m, resp.status_code, resp.text[:200])
            except Exception as exc:
                logger.warning("Gemini %s call failed: %s", m, exc)

        return None

    def synthesize_speech(self, text: str) -> str | None:
        """Synthesize speech with Gemini TTS. Returns a playable WAV data URI, or
        None so the browser speaks the reply itself (frontend speechSynthesis).

        Gemini TTS models require responseModalities=["AUDIO"] and a voice, and
        return raw PCM (audio/L16) — which browsers can't play from a data URI,
        so we wrap it in a WAV header before returning.
        """
        if not self.api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.tts_model}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": text[:400]}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": self.tts_voice}}
                },
            },
        }
        try:
            with httpx.Client(timeout=6.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.debug("Gemini TTS %s: %s", resp.status_code, resp.text[:160])
                    return None
                parts = (
                    resp.json()
                    .get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [])
                )
                for part in parts:
                    inline = part.get("inlineData") or part.get("inline_data")
                    if inline and inline.get("data"):
                        mime = inline.get("mimeType") or inline.get("mime_type") or ""
                        return _pcm_to_wav_data_uri(inline["data"], mime)
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
            logger.debug("Gemini TTS fallback to browser speech synthesis: %s", exc)

        return None

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe speech audio using Gemini."""
        if not self.api_key:
            return MockLLMProvider().transcribe_audio(audio_bytes, mime_type)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.transcribe_model}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
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
                resp = client.post(url, headers=headers, json=payload)
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


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI provider: tool-calling chat, TTS, STT, and moderation.

    Models (all overridable via env):
      OPENAI_MODEL             gpt-4o-mini        — agent reasoning + tool calls
      OPENAI_TTS_MODEL         gpt-4o-mini-tts    — speech synthesis (audio_url)
      OPENAI_TRANSCRIBE_MODEL  gpt-4o-transcribe  — speech-to-text (/transcribe)
      OPENAI_MODERATION_MODEL  omni-moderation-latest (free)
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.chat_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.tts_model = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
        self.tts_voice = os.getenv("OPENAI_TTS_VOICE", "alloy")
        self.transcribe_model = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe")
        self.moderation_model = os.getenv("OPENAI_MODERATION_MODEL", "omni-moderation-latest")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def generate_response(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        if not self.api_key:
            return MockLLMProvider().generate_response(prompt, system_instruction)
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json={"model": self.chat_model, "messages": messages, "max_tokens": 500},
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
                logger.warning("OpenAI chat error %s: %s", resp.status_code, resp.text[:200])
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("OpenAI chat call failed: %s", exc)
        return MockLLMProvider().generate_response(prompt, system_instruction)

    def chat_with_tools(self, messages: list[dict], tools: list[dict]) -> dict | None:
        if not self.api_key:
            return None
        payload: dict = {
            "model": self.chat_model,
            "messages": messages,
            "max_tokens": 500,
        }
        # An empty tool list means "reply in prose now" (the loop's final
        # summarise turn); the API rejects tools=[] so omit the keys entirely.
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        try:
            with httpx.Client(timeout=25.0) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]
                logger.warning("OpenAI tools error %s: %s", resp.status_code, resp.text[:200])
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("OpenAI tool-calling failed: %s", exc)
        return None

    def synthesize_speech(self, text: str) -> str | None:
        if not self.api_key:
            return None
        try:
            with httpx.Client(timeout=25.0) as client:
                resp = client.post(
                    f"{self.base_url}/audio/speech",
                    headers=self._headers(),
                    json={
                        "model": self.tts_model,
                        "voice": self.tts_voice,
                        "input": text[:800],
                        "response_format": "mp3",
                    },
                )
                if resp.status_code == 200:
                    b64 = base64.b64encode(resp.content).decode("ascii")
                    return f"data:audio/mp3;base64,{b64}"
                logger.debug("OpenAI TTS error %s", resp.status_code)
        except httpx.HTTPError as exc:
            logger.debug("OpenAI TTS failed: %s", exc)
        return None

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        if not self.api_key:
            return ""
        ext = mime_type.split("/")[-1].split(";")[0] or "wav"
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers=self._headers(),
                    data={"model": self.transcribe_model},
                    files={"file": (f"audio.{ext}", audio_bytes, mime_type)},
                )
                if resp.status_code == 200:
                    return resp.json().get("text", "").strip()
                logger.warning("OpenAI STT error %s: %s", resp.status_code, resp.text[:200])
        except (httpx.HTTPError, json.JSONDecodeError, ValueError) as exc:
            logger.warning("OpenAI STT failed: %s", exc)
        return ""

    def moderate(self, text: str) -> bool:
        if not self.api_key:
            return False
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{self.base_url}/moderations",
                    headers=self._headers(),
                    json={"model": self.moderation_model, "input": text},
                )
                if resp.status_code == 200:
                    return bool(resp.json()["results"][0]["flagged"])
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.debug("OpenAI moderation skipped: %s", exc)
        return False


def get_llm_provider(name: str | None = None) -> BaseLLMProvider:
    provider_name = (name or os.getenv("BOL_KE_APPLY_LLM_PROVIDER", "auto")).lower()
    if provider_name == "mock":
        return MockLLMProvider()
    if provider_name == "openai":
        return OpenAILLMProvider()
    if provider_name == "gemini":
        return GeminiLLMProvider()
    # auto: prefer OpenAI when its key exists, then Gemini, else mock (§10.4:
    # one provider at a time — decided by configuration, not by code).
    if os.getenv("OPENAI_API_KEY"):
        return OpenAILLMProvider()
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return GeminiLLMProvider()
    return MockLLMProvider()
