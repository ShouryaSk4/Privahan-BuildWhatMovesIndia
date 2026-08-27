"""Unit and integration tests for Driving Academy Assistant (Module 4)."""

from academy_service.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_catalog_has_10_curated_topics():
    """Verify catalog has approximately 10 video clips as required by AGENTS.md."""
    response = client.get("/academy/videos")
    assert response.status_code == 200
    videos = response.json()
    assert len(videos) == 10
    topics = [v["topic"] for v in videos]
    assert "8-turn" in topics
    assert "reverse parking" in topics
    assert "hill start" in topics
    assert "clutch control" in topics
    assert "steering" in topics


def test_match_eight_turn_query():
    payload = {
        "applicant_id": "app_123",
        "query": "I am having trouble steering properly on the 8 track test",
        "journey_stage": "practice_window",
    }
    response = client.post("/academy/match-video", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "8-turn"
    assert data["confidence"] > 0.5
    assert data["video_id"] == "vid_01_eight_turn"


def test_match_hill_start_query():
    payload = {
        "applicant_id": "app_123",
        "query": "Car rolls backward when starting uphill on the slope ramp",
        "journey_stage": "practice_window",
    }
    response = client.post("/academy/match-video", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "hill start"
    assert data["confidence"] > 0.5


def test_match_clutch_control_query():
    payload = {
        "applicant_id": "app_123",
        "query": "My engine keeps stalling when releasing the clutch",
        "journey_stage": "practice_window",
    }
    response = client.post("/academy/match-video", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "clutch control"
    assert data["confidence"] > 0.5


def test_match_unknown_fallback():
    payload = {
        "applicant_id": "app_123",
        "query": "What is the capital city of France?",
    }
    response = client.post("/academy/match-video", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] < 0.5
    assert data["fallback_message"] is not None
