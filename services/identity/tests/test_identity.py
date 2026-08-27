"""Unit and integration tests for Identity Service (Module 3)."""

from fastapi.testclient import TestClient
from identity_service.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_fetch_identity_clean_case():
    response = client.get("/identity/fetch/applicant_001")
    assert response.status_code == 200
    data = response.json()
    assert data["applicant_id"] == "applicant_001"
    assert data["name"] == "Rohan Verma"
    assert data["source"] == "digilocker_aadhaar"
    assert data["addresses_match"] is True


def test_student_mover_location_separation():
    """GPS suggested RTO and Aadhaar jurisdiction must be surfaced separately."""
    response = client.get(
        "/identity/fetch/applicant_student?gps_suggested_rto=KA-05%20Jayanagar"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gps_suggested_rto"] == "KA-05 Jayanagar"
    assert "Lucknow" in data["aadhaar_registered_address"]
    # Addresses match must be false because UP != KA
    assert data["addresses_match"] is False


def test_mismatch_check_pan_discrepancy():
    response = client.get("/identity/mismatch-check/applicant_mismatch")
    assert response.status_code == 200
    data = response.json()
    assert data["clear_to_submit"] is False
    assert len(data["mismatches"]) > 0
    assert any(m["field"] == "name" for m in data["mismatches"])


def test_mismatch_check_clean():
    response = client.get("/identity/mismatch-check/applicant_001")
    assert response.status_code == 200
    data = response.json()
    assert data["clear_to_submit"] is True
    assert len(data["mismatches"]) == 0
