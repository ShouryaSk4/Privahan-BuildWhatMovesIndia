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
        self.seen_tools: list[list[dict]] = []

    def generate_response(self, prompt, system_instruction=None):
        return "text"

    def synthesize_speech(self, text):
        return None

    def transcribe_audio(self, audio_bytes, mime_type="audio/wav"):
        return ""

    def chat_with_tools(self, messages, tools):
        self.seen.append(messages)
        self.seen_tools.append(tools)
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


def test_registry_covers_all_tools():
    names = {t["function"]["name"] for t in TOOL_SPECS}
    assert names == set(TOOL_EXECUTORS)
    assert len(names) == 13
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
    assert len(tools) == 13
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


def test_run_goal_stops_after_repeated_failures_with_summary():
    """Three consecutive failing actions must end the run as 'blocked' with a
    model-written summary — not spin until the step budget dies."""
    provider = ScriptedProvider(
        [
            tool_turn("start_application", {"applicant_id": "a1"}),
            tool_turn("start_application", {"applicant_id": "a2"}, "c2"),
            tool_turn("start_application", {"applicant_id": "a3"}, "c3"),
            {"role": "assistant", "content": "Blocked: journey service unreachable. Try later."},
        ]
    )
    out = run_goal(make_agent(provider), "apply for me", "applicant_clean", max_steps=10)
    assert out["stopped"] == "blocked"
    assert len(out["steps"]) == 3
    assert out["reply"].startswith("Blocked:")
    # the summary turn must carry no tools (prose-only wrap-up)
    assert provider.seen_tools[-1] == []


def test_run_goal_remembers_every_failed_signature():
    """A failed call may not be replayed later in the run, even after a
    successful call in between (the old rail only remembered the last one)."""
    fail = {"applicant_id": "applicant_clean"}
    provider = ScriptedProvider(
        [
            tool_turn("start_application", fail),
            tool_turn("whats_next", {"applicant_id": "applicant_clean"}, "c2"),  # ok (fallback)
            tool_turn("start_application", fail, "c3"),  # replay of the old failure
            {"role": "assistant", "content": "done"},
        ]
    )
    out = run_goal(make_agent(provider), "apply", "applicant_clean", max_steps=10)
    assert out["steps"][2]["result"]["error"] == "repeat_of_failed_call"


def test_interact_tool_loop_ends_with_prose_not_keyword_fallback():
    """When the turn budget is hit mid-tool-use, the agent asks for a prose
    wrap-up instead of silently dropping to the keyword engine."""
    turns = [tool_turn("whats_next", {"applicant_id": "a"}, f"c{i}") for i in range(6)]
    turns.append({"role": "assistant", "content": "Aapki journey shuru nahi hui hai."})
    provider = ScriptedProvider(turns)
    agent = make_agent(provider)
    out = agent._interact_with_tools("status batao", "applicant_clean", None, "hinglish")
    assert out is not None
    assert out["reply"].startswith("Aapki journey")


def test_journey_session_token_is_cached(monkeypatch):
    """One mint per applicant per TTL window — not one per tool call."""
    import bol_ke_apply.server as srv

    mints = []
    monkeypatch.setattr(srv, "_mint_session", lambda aid: mints.append(aid) or "tok_123")
    srv._session_cache.clear()
    h1 = srv._journey_headers("cache_test")
    h2 = srv._journey_headers("cache_test")
    assert h1 == h2 == {"Authorization": "Bearer tok_123"}
    assert mints == ["cache_test"]
    srv._session_cache.clear()
