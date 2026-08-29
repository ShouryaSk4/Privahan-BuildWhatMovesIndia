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
    assert "lane change" in topics
    assert "parallel parking" in topics
    assert "emergency braking" in topics
    assert "mirror and signal checks" in topics
    assert "gradient descent" in topics


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


def test_match_hinglish_clutch_query():
    """Verify Hinglish queries are correctly mapped to clutch control."""
    payload = {
        "applicant_id": "app_123",
        "query": "clutch kaise chhodna hai gadi bar bar band ho jaati hai",
        "journey_stage": "practice_window",
    }
    response = client.post("/academy/match-video", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "clutch control"
    assert data["confidence"] > 0.5


def test_match_hinglish_hill_start_query():
    """Verify Hinglish queries for hill start incline rollback."""
    payload = {
        "applicant_id": "app_123",
        "query": "chadhai par gadi peeche ja rahi hai handbrake kaise lagaye",
        "journey_stage": "practice_window",
    }
    response = client.post("/academy/match-video", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "hill start"
    assert data["confidence"] > 0.5


def test_match_hindi_script_query():
    """Verify Hindi Devanagari queries are correctly classified."""
    payload = {
        "applicant_id": "app_123",
        "query": "रिवर्स पार्किंग का सही तरीका बताएं",
        "journey_stage": "practice_window",
    }
    response = client.post("/academy/match-video", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "reverse parking"
    assert data["confidence"] > 0.5


def test_match_hinglish_gradient_descent_query():
    payload = {
        "applicant_id": "app_123",
        "query": "dhalaan se utarna hai brake garam ho jata hai",
    }
    response = client.post("/academy/match-video", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "gradient descent"
    assert data["confidence"] > 0.5


def test_match_unknown_fallback():
    payload = {
        "applicant_id": "app_123",
        "query": "What is the capital city of France?",
    }
    response = client.post("/academy/match-video", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] < 0.4
    assert data["fallback_message"] is not None


def test_rag_ask_incline_manual():
    """Verify RAG over the official RTO Complete Driving Manual."""
    payload = {
        "applicant_id": "app_123",
        "query": "What is the clutch bite point technique for hill start on an incline ramp?",
    }
    response = client.post("/academy/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["source_sections"]) > 0
    assert data["matched_video"] is not None
    assert data["matched_video"]["topic"] == "hill start"


def test_rag_ask_traffic_rules():
    """Verify RAG retrieval for road signs and legal rules."""
    payload = {
        "applicant_id": "app_123",
        "query": "What are mandatory traffic signs under Motor Vehicles Act?",
    }
    response = client.post("/academy/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["source_sections"]) > 0
    assert any("Traffic Signs" in s or "Legal" in s for s in data["source_sections"])
