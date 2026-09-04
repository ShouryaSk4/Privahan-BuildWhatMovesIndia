"""Module 6 — autonomous agent tests (CI-safe, no network, no API keys).

The journey service is not running during tests, so action tools return
structured `journey_unreachable` errors — which is exactly what the rails
(step budget, repeat-failure guard, honest stop reasons) must handle.
"""

import json
import os

import pytest
from bol_ke_apply.agent import (
    ACTION_TOOLS,
    TOOL_EXECUTORS,
    TOOL_SPECS,
    BolKeApplyAgent,
    run_goal,
)
from bol_ke_apply.api import app
from bol_ke_apply.llm_client import BaseLLMProvider, MockLLMProvider
from fastapi.testclient import TestClient

client = TestClient(app)


class ScriptedProvider(BaseLLMProvider):
    """Plays back a fixed sequence of assistant turns."""

    def __init__(self, turns):
        self.turns = list(turns)
        self.seen: list[list[dict]] = []

    def generate_response(self, prompt, system_instruction=None):
        return "text"

    def synthesize_speech(self, text):
        return None

    def transcribe_audio(self, audio_bytes, mime_type="audio/wav"):
        return ""

    def chat_with_tools(self, messages, tools):
        self.seen.append(messages)
        return self.turns.pop(0) if self.turns else {"role": "assistant", "content": "done"}


def tool_turn(name, args, call_id="c1"):
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)},
            }
        ],
    }


def make_agent(provider):
    agent = BolKeApplyAgent.__new__(BolKeApplyAgent)
    agent.provider = provider
    return agent


@pytest.fixture(autouse=True)
def hermetic_journey(monkeypatch):
    """Point action tools at an unroutable port: tests must not touch a live
    dev journey service (side effects) and must be deterministic offline."""
    import bol_ke_apply.server as srv

    monkeypatch.setattr(srv, "JOURNEY_SERVICE_URL", "http://127.0.0.1:1")


def test_registry_covers_all_ten_tools():
    names = {t["function"]["name"] for t in TOOL_SPECS}
    assert names == set(TOOL_EXECUTORS)
    assert len(names) == 10
    assert ACTION_TOOLS <= names


def test_run_goal_executes_steps_and_logs_them():
    provider = ScriptedProvider(
        [
            tool_turn("whats_next", {"applicant_id": "applicant_clean"}),
            tool_turn("start_application", {"applicant_id": "applicant_clean"}, "c2"),
            {"role": "assistant", "content": "Application step attempted; journey unreachable."},
        ]
    )
    out = run_goal(make_agent(provider), "get my licence started", "applicant_clean")
    assert [s["tool"] for s in out["steps"]] == ["whats_next", "start_application"]
    assert out["stopped"] == "completed"
    assert out["reply"].startswith("Application step attempted")
    # whats_next has an offline fallback (ok), start_application reports unreachable
    assert out["steps"][0]["ok"] is True
    assert out["steps"][1]["ok"] is False


def test_run_goal_blocks_verbatim_retry_of_failed_call():
    same = {"applicant_id": "applicant_clean"}
    provider = ScriptedProvider(
        [
            tool_turn("start_application", same),
            tool_turn("start_application", same, "c2"),  # identical retry
            {"role": "assistant", "content": "stopping"},
        ]
    )
    out = run_goal(make_agent(provider), "start my application", "applicant_clean")
    assert out["steps"][1]["result"]["error"] == "repeat_of_failed_call"


def test_run_goal_respects_step_budget():
    endless = [tool_turn("whats_next", {"applicant_id": "a"}, f"c{i}") for i in range(30)]
    out = run_goal(make_agent(ScriptedProvider(endless)), "loop forever", "applicant_clean", max_steps=4)
    assert out["stopped"] == "max_steps"
    assert len(out["steps"]) == 4


def test_run_goal_without_tool_provider_says_so():
    out = run_goal(make_agent(MockLLMProvider()), "start my application", "applicant_clean")
    assert out["stopped"] == "no_provider"
    assert out["steps"] == []


def test_agent_run_endpoint_shape():
    res = client.post(
        "/agent/run", json={"goal": "check my status", "applicant_id": "applicant_clean"}
    )
    assert res.status_code == 200
    body = res.json()
    assert {"reply", "steps", "stopped", "engine"} <= set(body)


def test_tools_endpoint_marks_consequential_actions():
    tools = client.get("/tools").json()
    assert len(tools) == 10
    flags = {t["name"]: t["consequential"] for t in tools}
    assert flags["book_test_slot"] is True
    assert flags["whats_next"] is False


# ---------------------------------------------------------------- live eval

AUTONOMY_EVALS = [
    "meri learner licence application shuru karo, jurisdiction Aadhaar wala choose karna",
    "check my journey status and tell me the next step",
]


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="live eval needs OPENAI_API_KEY")
@pytest.mark.parametrize("goal", AUTONOMY_EVALS)
def test_live_autonomous_goal(goal):
    agent = BolKeApplyAgent(provider_name="openai")
    out = run_goal(agent, goal, "applicant_clean", max_steps=8)
    assert out["reply"]
    assert out["stopped"] in ("completed", "max_steps")
    assert all("tool" in s for s in out["steps"])
