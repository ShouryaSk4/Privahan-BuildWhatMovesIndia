"""Module 6 — OpenAI tool-calling agent tests.

CI-safe: everything here runs against fakes. The live eval at the bottom only
runs when OPENAI_API_KEY is present (developer machines / nightly), so the
suite never needs network in CI.
"""

import json
import os

import pytest
from bol_ke_apply.agent import (
    TOOL_EXECUTORS,
    TOOL_SPECS,
    BolKeApplyAgent,
    reset_history,
)
from bol_ke_apply.api import app
from bol_ke_apply.llm_client import BaseLLMProvider, MockLLMProvider, get_llm_provider
from fastapi.testclient import TestClient

client = TestClient(app)


# ---------------------------------------------------------------- fakes


class FakeToolCallingProvider(BaseLLMProvider):
    """Scripted provider: first turn calls whats_next, second turn answers."""

    def __init__(self):
        self.calls = 0
        self.seen_messages: list[list[dict]] = []

    def generate_response(self, prompt, system_instruction=None):
        return "fallback text"

    def synthesize_speech(self, text):
        return None

    def transcribe_audio(self, audio_bytes, mime_type="audio/wav"):
        return "namaste"

    def chat_with_tools(self, messages, tools):
        self.seen_messages.append(messages)
        self.calls += 1
        if self.calls == 1:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "whats_next",
                            "arguments": json.dumps({"applicant_id": "applicant_clean"}),
                        },
                    }
                ],
            }
        return {"role": "assistant", "content": "Aapka application abhi shuru nahi hua hai."}


class FlaggingProvider(MockLLMProvider):
    def moderate(self, text):
        return True


class ToollessProvider(MockLLMProvider):
    """chat_with_tools inherits the base None — agent must fall back to keywords."""


# ---------------------------------------------------------------- tool specs


def test_tool_specs_come_from_contracts():
    names = {t["function"]["name"] for t in TOOL_SPECS}
    assert names == {"fetch_identity", "check_mismatch", "match_video", "whats_next"}
    for spec in TOOL_SPECS:
        params = spec["function"]["parameters"]
        assert "applicant_id" in params["properties"], spec["function"]["name"]
        assert spec["function"]["description"]
    assert set(TOOL_EXECUTORS) == names


# ---------------------------------------------------------------- agent loop


def test_agent_executes_native_tool_calls_and_replies():
    reset_history("applicant_clean")
    provider = FakeToolCallingProvider()
    agent = BolKeApplyAgent.__new__(BolKeApplyAgent)
    agent.provider = provider

    out = agent.interact("mera application status kya hai", applicant_id="applicant_clean")
    assert out["tool_called"] == "whats_next"
    assert out["tool_result"]["applicant_id"] == "applicant_clean"
    assert out["reply"] == "Aapka application abhi shuru nahi hua hai."
    assert out["engine"] == "FakeToolCallingProvider"
    # second model turn received the tool result message
    tool_msgs = [m for m in provider.seen_messages[1] if m.get("role") == "tool"]
    assert tool_msgs and "current_stage" in tool_msgs[0]["content"]


def test_agent_keeps_conversation_history():
    reset_history("applicant_clean")
    provider = FakeToolCallingProvider()
    agent = BolKeApplyAgent.__new__(BolKeApplyAgent)
    agent.provider = provider
    agent.interact("mera application status kya hai", applicant_id="applicant_clean")

    provider.calls = 1  # next turn answers directly (no tool round)
    agent.interact("aur uske baad?", applicant_id="applicant_clean")
    # the second request's messages must include the first exchange
    history_roles = [m["role"] for m in provider.seen_messages[-1]]
    assert history_roles.count("assistant") >= 1
    assert any(
        "status kya hai" in (m.get("content") or "") for m in provider.seen_messages[-1]
    )


def test_agent_falls_back_to_keywords_without_tool_support():
    agent = BolKeApplyAgent(provider_name="mock")
    out = agent.interact("Mera verified Aadhaar profile dikhao", applicant_id="applicant_clean")
    assert out["tool_called"] == "fetch_identity"
    assert out["engine"].endswith("+keywords")


def test_moderation_refuses_politely():
    agent = BolKeApplyAgent.__new__(BolKeApplyAgent)
    agent.provider = FlaggingProvider()
    out = agent.interact("some harmful request", applicant_id="applicant_clean")
    assert out["tool_called"] is None
    assert out["engine"] == "moderation"
    assert "licence" in out["reply"].lower() or "लाइसेंस" in out["reply"]


# ---------------------------------------------------------------- API surface


def test_transcribe_endpoint_rejects_bad_payload():
    assert client.post("/transcribe", json={"audio_b64": "!!!not-base64!!!"}).status_code in (
        400,
        502,
    )


def test_transcribe_endpoint_with_mock_provider():
    import base64

    res = client.post(
        "/transcribe",
        json={"audio_b64": base64.b64encode(b"fake-audio").decode(), "mime_type": "audio/webm"},
    )
    # mock provider returns a canned transcript; providers without STT yield 502
    assert res.status_code in (200, 502)
    if res.status_code == 200:
        assert res.json()["text"]


def test_provider_selection_explicit_openai():
    provider = get_llm_provider("openai")
    assert type(provider).__name__ == "OpenAILLMProvider"


# ---------------------------------------------------------------- live evals

EVALS = [
    ("mera application status kya hai", "whats_next"),
    ("what stage is my licence application at?", "whats_next"),
    ("aage kya karna hai mujhe?", "whats_next"),
    ("mera aadhaar profile dikhao", "fetch_identity"),
    ("kya mere documents me koi galti hai jo reject ho sakti hai?", "check_mismatch"),
    ("reverse parking kaise karte hain?", "match_video"),
    ("गाड़ी ढलान पर पीछे जाती है, क्या करूं?", "match_video"),
    ("I keep stalling the car when starting on a hill", "match_video"),
]


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="live eval needs OPENAI_API_KEY")
@pytest.mark.parametrize(("utterance", "expected_tool"), EVALS)
def test_live_eval_tool_routing(utterance, expected_tool):
    reset_history("applicant_clean")
    agent = BolKeApplyAgent(provider_name="openai")
    out = agent.interact(utterance, applicant_id="applicant_clean")
    assert out["tool_called"] == expected_tool, f"{utterance!r} -> {out['tool_called']}"
    assert out["reply"]
