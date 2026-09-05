"""Security + server-authoritative exam tests for Module 2.

These run the REAL auth gates (no dependency overrides), so they prove the
holes flagged in the security review are actually closed.
"""

import pytest
from contracts.security import (
    check_service_token,
    mint_session,
    verify_session,
)
from fastapi.testclient import TestClient

from journey_service import exam as exam_mod
from journey_service.engine import reset_engine
from journey_service.main import app


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("IDENTITY_MODE", "stub")
    monkeypatch.setenv("JOURNEY_DB", ":memory:")
    reset_engine()
    return TestClient(app)


def auth(applicant_id: str) -> dict:
    return {"Authorization": f"Bearer {mint_session(applicant_id)}"}


# --- session tokens ---------------------------------------------------------


def test_session_roundtrip_and_expiry():
    tok = mint_session("applicant_001", ttl=100, now=1000.0)
    assert verify_session(tok, now=1050.0) == "applicant_001"
    assert verify_session(tok, now=2000.0) is None  # expired
    assert verify_session("garbage") is None
    assert verify_session(None) is None


def test_tampered_token_is_rejected():
    tok = mint_session("applicant_001")
    body, sig = tok.split(".", 1)
    forged = f"{body}.{'0' * len(sig)}"
    assert verify_session(forged) is None


def test_service_token_constant_time_check():
    from contracts.security import service_token

    assert check_service_token(service_token()) is True
    assert check_service_token("wrong") is False
    assert check_service_token(None) is False


# --- ownership (IDOR closed) -------------------------------------------------


def test_journey_requires_session_token(client):
    assert client.get("/journey/applicant_001").status_code == 401


def test_session_cannot_touch_another_applicant(client):
    # A token for applicant_001 must not read applicant_student's journey.
    res = client.get("/journey/applicant_student", headers=auth("applicant_001"))
    assert res.status_code == 403


def test_owner_can_read_own_journey(client):
    res = client.get("/journey/applicant_001", headers=auth("applicant_001"))
    assert res.status_code == 200
    assert res.json()["current_stage"] == "no_licence"


def test_session_endpoint_mints_for_the_requested_id(client):
    res = client.post("/session", json={"applicant_id": "applicant_777"})
    assert res.status_code == 200
    assert verify_session(res.json()["token"]) == "applicant_777"


# --- server-authoritative exam ----------------------------------------------


def test_exam_paper_never_leaks_the_answer_key(client):
    res = client.get("/journey/applicant_001/ll-exam", headers=auth("applicant_001"))
    assert res.status_code == 200
    paper = res.json()
    assert paper["questions"]
    for q in paper["questions"]:
        assert "correct" not in q  # the answer key stays on the server
        assert "options" in q


def test_exam_grades_on_the_server_not_the_client():
    # All-correct passes; all-wrong fails — computed here, in Python.
    correct = [q["correct"] for q in exam_mod._QUESTIONS]
    passed = exam_mod.grade(exam_mod.ExamSubmission(answers=correct))
    assert passed.passed and passed.score == len(correct)

    wrong = [(q["correct"] + 1) % len(q["options"]) for q in exam_mod._QUESTIONS]
    failed = exam_mod.grade(exam_mod.ExamSubmission(answers=wrong))
    assert not failed.passed


def test_exam_recomputes_integrity_tier_ignoring_client_claims():
    # The client could claim "clear"; the server derives the tier from events.
    sub = exam_mod.ExamSubmission(
        answers=[q["correct"] for q in exam_mod._QUESTIONS],
        integrity=exam_mod.IntegritySubmission(
            camera="on",
            events=[{"type": "tab_hidden"}, {"type": "multiple_faces"}, {"type": "tab_hidden"}],
        ),
    )
    result = exam_mod.grade(sub)
    # 100 - 12 - 15 - 12 = 61 → "review", regardless of any client-sent tier.
    assert result.integrity_score == 61
    assert result.integrity_tier == "review"


def test_exam_no_camera_never_clear():
    sub = exam_mod.ExamSubmission(
        answers=[q["correct"] for q in exam_mod._QUESTIONS],
        integrity=exam_mod.IntegritySubmission(camera="denied", events=[]),
    )
    result = exam_mod.grade(sub)
    assert result.integrity_score == 100  # equity: no score penalty
    assert result.integrity_tier == "review"  # but a human must look


def test_exam_submit_advances_stage_only_on_pass(client, monkeypatch):
    monkeypatch.setenv("GATEWAY_MODE", "direct")  # in-process gateway, no HTTP/token
    monkeypatch.setenv("GATEWAY_DB", ":memory:")
    from gateway_service.sarathi import reset_client

    reset_client()
    h = auth("applicant_001")
    # get to the test-open stage via the real apply (auto-verifies docs)
    assert client.post("/journey/applicant_001/apply", json={}, headers=h).status_code == 200

    correct = [q["correct"] for q in exam_mod._QUESTIONS]
    res = client.post("/journey/applicant_001/ll-exam", json={"answers": correct}, headers=h)
    assert res.status_code == 200
    body = res.json()
    assert body["result"]["passed"] is True
    assert body["state"]["current_stage"] == "ll_issued"
