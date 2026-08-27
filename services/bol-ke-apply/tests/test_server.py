"""Unit tests for Bol Ke Apply MCP Server (Module 6)."""

from bol_ke_apply.llm_client import MockLLMProvider, get_llm_provider
from bol_ke_apply.server import check_mismatch, fetch_identity, match_video


def test_fetch_identity_tool():
    result = fetch_identity(applicant_id="app_test_01")
    assert result["applicant_id"] == "app_test_01"
    assert "source" in result
    assert "photo_url" in result
    assert "gps_suggested_rto" in result
    assert "aadhaar_registered_address" in result


def test_check_mismatch_tool():
    result = check_mismatch(applicant_id="app_test_01")
    assert result["applicant_id"] == "app_test_01"
    assert "clear_to_submit" in result
    assert isinstance(result["mismatches"], list)


def test_match_video_tool():
    result = match_video(
        applicant_id="app_test_01",
        query="How do I do parallel parking?",
        journey_stage="practice_window",
    )
    assert "video_id" in result
    assert "topic" in result
    assert "confidence" in result


def test_llm_provider_fallback():
    provider = get_llm_provider("mock")
    assert isinstance(provider, MockLLMProvider)
    response = provider.generate_response("Hello, I need help with parking")
    assert "Driving Academy" in response
