"""Unit tests for Bol Ke Apply MCP Server, Agent, and API (Module 6)."""

from bol_ke_apply.agent import BolKeApplyAgent
from bol_ke_apply.api import app
from bol_ke_apply.llm_client import MockLLMProvider, get_llm_provider
from bol_ke_apply.server import check_mismatch, fetch_identity, match_video
from fastapi.testclient import TestClient

client = TestClient(app)


def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_tools_list():
    response = client.get("/tools")
    assert response.status_code == 200
    tools = response.json()
    names = [t["name"] for t in tools]
    assert "fetch_identity" in names
    assert "check_mismatch" in names
    assert "match_video" in names


def test_api_chat_endpoint():
    response = client.post(
        "/chat",
        json={"message": "Mera profile dikhao", "applicant_id": "applicant_clean"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tool_called"] == "fetch_identity"


def test_api_html_console():
    response = client.get("/")
    assert response.status_code == 200
    assert "बोल के अप्लाई" in response.text


def test_fetch_identity_tool():
    result = fetch_identity(applicant_id="applicant_clean")
    assert result["applicant_id"] == "applicant_clean"
    assert result["name"] == "Rohan Verma"
    assert result["source"] == "digilocker_aadhaar"
    assert result["addresses_match"] is True


def test_check_mismatch_clean_tool():
    result = check_mismatch(applicant_id="applicant_clean")
    assert result["applicant_id"] == "applicant_clean"
    assert result["clear_to_submit"] is True
    assert len(result["mismatches"]) == 0


def test_check_mismatch_pan_error_tool():
    result = check_mismatch(applicant_id="applicant_pan_name_mismatch")
    assert result["clear_to_submit"] is False
    assert any(m["field"] == "name" for m in result["mismatches"])


def test_match_video_tool():
    result = match_video(
        applicant_id="applicant_clean",
        query="How do I do parallel parking?",
        journey_stage="practice_window",
    )
    assert result["topic"] == "parallel parking"
    assert result["confidence"] > 0.5


def test_agent_multilingual_driving_academy_hinglish():
    agent = BolKeApplyAgent(provider_name="mock")
    interaction = agent.interact(
        message="clutch kaise chhodna hai gadi band ho jaati hai",
        applicant_id="applicant_clean",
    )
    assert interaction["tool_called"] == "match_video"
    assert interaction["tool_result"]["topic"] == "clutch control"
    assert interaction["language"] == "hinglish"


def test_agent_multilingual_driving_academy_hindi():
    agent = BolKeApplyAgent(provider_name="mock")
    interaction = agent.interact(
        message="रिवर्स पार्किंग का सही तरीका बताओ",
        applicant_id="applicant_clean",
    )
    assert interaction["tool_called"] == "match_video"
    assert interaction["tool_result"]["topic"] == "reverse parking"
    assert interaction["language"] == "hindi"


def test_agent_identity_fetch_interaction():
    agent = BolKeApplyAgent(provider_name="mock")
    interaction = agent.interact(
        message="Mera verified Aadhaar profile dikhao",
        applicant_id="applicant_clean",
    )
    assert interaction["tool_called"] == "fetch_identity"
    assert interaction["tool_result"]["name"] == "Rohan Verma"


def test_agent_mismatch_check_interaction():
    agent = BolKeApplyAgent(provider_name="mock")
    interaction = agent.interact(
        message="Check karo mere documents me koi mistake ya rejection risk to nahi hai",
        applicant_id="applicant_pan_name_mismatch",
    )
    assert interaction["tool_called"] == "check_mismatch"
    assert interaction["tool_result"]["clear_to_submit"] is False


def test_llm_provider_fallback():
    provider = get_llm_provider("mock")
    assert isinstance(provider, MockLLMProvider)
    response = provider.generate_response("Hello, I need help with parking")
    assert "Driving Academy" in response
