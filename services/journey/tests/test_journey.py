"""Module 2 local verification (AGENTS.md §8.6).

Gateway calls are faked at the client boundary; identity uses the stub client
(the default). No other module's code is imported.
"""

from datetime import UTC, datetime, timedelta

import pytest
from contracts.gateway import (
    GovApplicationStatus,
    GovSubmissionResult,
    LLApplicationSubmission,
    SlotBookingRequest,
    SlotBookingResult,
    TestSlot,
)
from fastapi.testclient import TestClient

from app.clients.gateway import GatewayClient, get_gateway_client
from app.engine import get_engine, reset_engine
from app.main import app


class FakeGatewayClient(GatewayClient):
    """In-memory stand-in for Module 5, implementing the same client surface."""

    def __init__(self) -> None:
        self.gov_stage = "received"
        self.failed_checkpoint = None
        self.submissions: list[LLApplicationSubmission] = []

    def submit_ll_application(self, submission):
        self.submissions.append(submission)
        return GovSubmissionResult(
            application_number="DL20260000001",
            status="received",
            submitted_at=datetime.now(UTC),
        )

    def get_application_status(self, application_number):
        return GovApplicationStatus(
            application_number=application_number,
            applicant_id="whoever",
            stage=self.gov_stage,
            updated_at=datetime.now(UTC),
            failed_checkpoint=self.failed_checkpoint,
        )

    def list_dl_test_slots(self, rto_code):
        return [
            TestSlot(
                slot_id=f"{rto_code}-1-9",
                rto_code=rto_code,
                starts_at=datetime.now(UTC) + timedelta(days=1),
                capacity_left=5,
            )
        ]

    def book_dl_test(self, request: SlotBookingRequest):
        slot = self.list_dl_test_slots("DL01")[0]
        return SlotBookingResult(booking_id="BK0000001", slot=slot, confirmed=True)


@pytest.fixture()
def fake_gateway():
    return FakeGatewayClient()


@pytest.fixture()
def client(fake_gateway, monkeypatch):
    monkeypatch.setenv("JOURNEY_FAST_FORWARD", "1")
    reset_engine()
    app.dependency_overrides[get_gateway_client] = lambda: fake_gateway
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_new_applicant_starts_at_no_licence(client):
    body = client.get("/journey/APL-0001").json()
    assert body["current_stage"] == "no_licence"
    assert body["next_action"]["type"] == "start_application"
    assert body["certainty"] == {"cost_inr": 1350, "eta_days": 21, "visit_count": 1}
    assert any(d["code"] == "aadhaar_ekyc" for d in body["required_documents"])


def test_agents_md_7_4_reference_shape(client):
    """The practice_window response must carry the exact §7.4 reference values."""
    engine = get_engine()
    for event in ("ll_application_submitted", "documents_verified", "ll_test_passed", "begin_practice"):
        engine.apply_event("APL-0001", event)

    body = client.get("/journey/APL-0001").json()
    reference = {
        "applicant_id": "APL-0001",
        "journey_type": "first_time_licence",
        "current_stage": "practice_window",
        "next_action": {"type": "book_dl_test", "label": "Book your driving test"},
        "certainty": {"cost_inr": 1350, "eta_days": 21, "visit_count": 1},
    }
    for key, expected in reference.items():
        assert body[key] == expected, f"§7.4 drift on '{key}'"


def test_illegal_transition_conflicts(client):
    res = client.post("/journey/APL-0001/events", json={"event": "dl_test_passed"})
    assert res.status_code == 409


def test_zero_form_apply_uses_verified_identity(client, fake_gateway):
    res = client.post("/journey/APL-0001/apply", json={})
    assert res.status_code == 200
    body = res.json()
    assert body["current_stage"] == "ll_application_submitted"
    assert body["application_number"] == "DL20260000001"
    # The submission was assembled from Module 3's verified profile, not user input.
    assert fake_gateway.submissions[0].name == "Asha Sharma"


def test_rejection_prevention_blocks_mismatched_records(client):
    res = client.post("/journey/APL-0009/apply", json={})
    assert res.status_code == 422
    detail = res.json()["detail"]
    assert detail["reason"] == "rejection_prevention"
    assert detail["mismatches"][0]["field"] == "name"


def test_rto_disagreement_is_surfaced_not_silently_resolved(client):
    # Stub convention: applicant ids ending in "2" have GPS/Aadhaar RTO disagreement.
    res = client.post("/journey/APL-0002/apply", json={})
    assert res.status_code == 409
    assert res.json()["detail"]["reason"] == "rto_confirmation_required"

    # Explicit confirmation resolves it.
    res = client.post("/journey/APL-0002/apply", json={"confirmed_rto_code": "UP32"})
    assert res.status_code == 200


def test_practice_window_gate_blocks_early_booking(client, monkeypatch):
    monkeypatch.delenv("JOURNEY_FAST_FORWARD", raising=False)
    engine = get_engine()
    engine.record("APL-0001").application_number = "DL20260000001"
    for event in ("ll_application_submitted", "documents_verified", "ll_test_passed", "begin_practice"):
        engine.apply_event("APL-0001", event)

    res = client.post("/journey/APL-0001/dl-test/bookings", json={"slot_id": "DL01-1-9"})
    assert res.status_code == 409
    assert "practice window" in res.json()["detail"]


def test_full_journey_with_fast_forward(client, fake_gateway):
    client.post("/journey/APL-0001/apply", json={})
    fake_gateway.gov_stage = "documents_verified"
    body = client.post("/journey/APL-0001/sync").json()
    assert body["current_stage"] == "ll_documents_verified"

    fake_gateway.gov_stage = "ll_issued"
    body = client.post("/journey/APL-0001/sync").json()
    assert body["current_stage"] == "ll_issued"

    client.post("/journey/APL-0001/events", json={"event": "begin_practice"})
    body = client.post("/journey/APL-0001/dl-test/bookings", json={"slot_id": "DL01-1-9"}).json()
    assert body["current_stage"] == "dl_test_booked"

    # Failed test syncs in with its checkpoint, feeding Academy coaching.
    fake_gateway.gov_stage = "dl_test_failed"
    fake_gateway.failed_checkpoint = "reverse_parking"
    body = client.post("/journey/APL-0001/sync").json()
    assert body["current_stage"] == "dl_test_result_fail"
    assert "reverse_parking" in body["stage_detail"]

    # Rebook, pass, licence issued.
    client.post("/journey/APL-0001/dl-test/bookings", json={"slot_id": "DL01-1-9"})
    fake_gateway.gov_stage = "dl_issued"
    body = client.post("/journey/APL-0001/sync").json()
    assert body["current_stage"] == "dl_issued"
    assert body["next_action"]["type"] == "journey_complete"


def test_sync_never_regresses_practice_window(client, fake_gateway):
    client.post("/journey/APL-0001/apply", json={})
    fake_gateway.gov_stage = "ll_issued"
    client.post("/journey/APL-0001/sync")
    client.post("/journey/APL-0001/events", json={"event": "begin_practice"})

    # Gov side still says ll_issued; local practice_window must survive the sync.
    body = client.post("/journey/APL-0001/sync").json()
    assert body["current_stage"] == "practice_window"
