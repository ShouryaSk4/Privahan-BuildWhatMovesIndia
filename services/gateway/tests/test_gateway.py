"""Module 5 local verification (AGENTS.md §8.6) — full mock journey through the gateway."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.sarathi import reset_client


@pytest.fixture()
def client():
    reset_client()
    return TestClient(app)


SUBMISSION = {
    "applicant_id": "APL-0001",
    "name": "Asha Sharma",
    "dob": "2002-03-14",
    "address": "12 Patel Nagar, New Delhi",
    "photo_url": "https://example.invalid/photo.jpg",
    "rto_code": "DL01",
    "vehicle_class": "LMV",
}


def submit(client) -> str:
    res = client.post("/gov/ll-applications", json=SUBMISSION)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "received"
    return body["application_number"]


def test_submit_and_status(client):
    application_number = submit(client)
    res = client.get(f"/gov/applications/{application_number}")
    assert res.status_code == 200
    assert res.json()["stage"] == "received"
    assert res.json()["applicant_id"] == "APL-0001"


def test_unknown_application_404(client):
    assert client.get("/gov/applications/DL0000000").status_code == 404


def test_full_first_time_licence_journey(client):
    application_number = submit(client)

    # RTO verifies documents
    res = client.post(f"/gov/applications/{application_number}/verify-documents")
    assert res.json()["stage"] == "documents_verified"

    # LL test passed -> LL issued
    res = client.post(
        "/gov/test-results",
        json={"application_number": application_number, "test_type": "ll", "passed": True},
    )
    assert res.json()["stage"] == "ll_issued"

    # Slots are visible and bookable
    slots = client.get("/gov/dl-test/slots", params={"rto_code": "DL01"}).json()
    assert len(slots) > 0
    res = client.post(
        "/gov/dl-test/bookings",
        json={
            "applicant_id": "APL-0001",
            "application_number": application_number,
            "slot_id": slots[0]["slot_id"],
        },
    )
    assert res.status_code == 200
    assert res.json()["confirmed"] is True

    # Fail the DL test, rebook, then pass
    res = client.post(
        "/gov/test-results",
        json={
            "application_number": application_number,
            "test_type": "dl",
            "passed": False,
            "failed_checkpoint": "reverse_parking",
        },
    )
    assert res.json()["stage"] == "dl_test_failed"

    res = client.post(
        "/gov/dl-test/bookings",
        json={
            "applicant_id": "APL-0001",
            "application_number": application_number,
            "slot_id": slots[1]["slot_id"],
        },
    )
    assert res.status_code == 200

    res = client.post(
        "/gov/test-results",
        json={"application_number": application_number, "test_type": "dl", "passed": True},
    )
    assert res.json()["stage"] == "dl_issued"


def test_cannot_book_dl_before_ll_issued(client):
    application_number = submit(client)
    res = client.post(
        "/gov/dl-test/bookings",
        json={
            "applicant_id": "APL-0001",
            "application_number": application_number,
            "slot_id": "DL01-1-9",
        },
    )
    assert res.status_code == 409


def test_ll_result_rejected_before_document_verification(client):
    application_number = submit(client)
    res = client.post(
        "/gov/test-results",
        json={"application_number": application_number, "test_type": "ll", "passed": True},
    )
    assert res.status_code == 409
