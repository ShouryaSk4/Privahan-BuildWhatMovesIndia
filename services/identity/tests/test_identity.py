"""Unit and integration tests for Identity Service (Module 3)."""

from fastapi.testclient import TestClient
from identity_service.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_personas():
    response = client.get("/identity/personas")
    assert response.status_code == 200
    personas = response.json()
    assert "applicant_clean" in personas
    assert "applicant_student_mover" in personas
    assert "applicant_pan_name_mismatch" in personas
    assert "applicant_minor" in personas
    assert "applicant_dob_mismatch" in personas


def test_fetch_identity_clean_case():
    response = client.get("/identity/fetch/applicant_clean")
    assert response.status_code == 200
    data = response.json()
    assert data["applicant_id"] == "applicant_clean"
    assert data["name"] == "Rohan Verma"
    assert data["source"] == "digilocker_aadhaar"
    assert data["addresses_match"] is True
    assert data["age"] >= 18
    assert data["age_eligible"] is True


def test_student_mover_location_separation():
    """GPS suggested RTO and Aadhaar jurisdiction must be surfaced separately."""
    response = client.get(
        "/identity/fetch/applicant_student_mover?gps_suggested_rto=KA-05%20Jayanagar"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gps_suggested_rto"] == "KA-05 Jayanagar"
    assert "Lucknow" in data["aadhaar_registered_address"]
    # Addresses match must be false because UP != KA
    assert data["addresses_match"] is False


def test_mismatch_check_pan_name_discrepancy():
    response = client.get("/identity/mismatch-check/applicant_pan_name_mismatch")
    assert response.status_code == 200
    data = response.json()
    assert data["clear_to_submit"] is False
    assert any(m["field"] == "name" and m["severity"] == "error" for m in data["mismatches"])


def test_mismatch_check_minor_applicant():
    """Under-18 applicants must be caught as ineligible for LMV licence."""
    response = client.get("/identity/mismatch-check/applicant_minor")
    assert response.status_code == 200
    data = response.json()
    assert data["clear_to_submit"] is False
    assert any("age" in m["issue"].lower() for m in data["mismatches"])


def test_mismatch_check_dob_discrepancy():
    response = client.get("/identity/mismatch-check/applicant_dob_mismatch")
    assert response.status_code == 200
    data = response.json()
    assert data["clear_to_submit"] is False
    assert any(m["field"] == "dob" and m["severity"] == "error" for m in data["mismatches"])


def test_mismatch_check_clean():
    response = client.get("/identity/mismatch-check/applicant_clean")
    assert response.status_code == 200
    data = response.json()
    assert data["clear_to_submit"] is True
    assert len(data["mismatches"]) == 0
