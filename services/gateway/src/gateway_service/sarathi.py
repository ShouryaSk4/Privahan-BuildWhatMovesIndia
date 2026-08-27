"""Sarathi client — the single swap point for eventual real government access.

`SarathiClient` is the interface the gateway's routes code against.
`MockSarathiClient` simulates the government side in memory, mirroring the
request/response shapes we expect from real Sarathi access (AGENTS.md §5.5,
§9.2). When real access arrives, implement `RealSarathiClient` against the
same protocol and change only `get_client()`.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta
from typing import Protocol

from contracts.gateway import (
    GovApplicationStatus,
    GovSubmissionResult,
    LLApplicationSubmission,
    SlotBookingRequest,
    SlotBookingResult,
    TestResultReport,
    TestSlot,
)


class SarathiError(Exception):
    """Raised for government-side rejections the gateway normalizes to HTTP errors."""


class SarathiClient(Protocol):
    def submit_ll_application(self, submission: LLApplicationSubmission) -> GovSubmissionResult: ...

    def get_application_status(self, application_number: str) -> GovApplicationStatus: ...

    def verify_documents(self, application_number: str) -> GovApplicationStatus: ...

    def list_dl_test_slots(self, rto_code: str) -> list[TestSlot]: ...

    def book_dl_test(self, request: SlotBookingRequest) -> SlotBookingResult: ...

    def report_test_result(self, report: TestResultReport) -> GovApplicationStatus: ...


# Government-side stages the mock walks through. These are the gateway's
# normalized names — Module 2 maps them onto journey_stage; nothing upstream
# ever sees raw Sarathi status codes.
GOV_STAGES = (
    "received",
    "documents_verified",
    "ll_test_passed",
    "ll_issued",
    "dl_test_booked",
    "dl_test_failed",
    "dl_test_passed",
    "dl_issued",
)


class MockSarathiClient:
    """In-memory simulation of Sarathi for the MVP.

    Deliberately stateful: submissions, slots, and bookings persist for the
    process lifetime so the full first-time-licence journey can be exercised
    end to end without government access.
    """

    def __init__(self) -> None:
        self._applications: dict[str, GovApplicationStatus] = {}
        self._bookings: dict[str, SlotBookingResult] = {}
        self._slot_capacity: dict[str, int] = {}
        self._app_seq = itertools.count(1)
        self._booking_seq = itertools.count(1)

    # -- LL application -------------------------------------------------

    def submit_ll_application(self, submission: LLApplicationSubmission) -> GovSubmissionResult:
        now = datetime.now(UTC)
        application_number = f"DL{now.year}{next(self._app_seq):07d}"
        self._applications[application_number] = GovApplicationStatus(
            application_number=application_number,
            applicant_id=submission.applicant_id,
            stage="received",
            updated_at=now,
        )
        return GovSubmissionResult(
            application_number=application_number, status="received", submitted_at=now
        )

    def get_application_status(self, application_number: str) -> GovApplicationStatus:
        status = self._applications.get(application_number)
        if status is None:
            raise SarathiError(f"Unknown application number: {application_number}")
        return status

    def verify_documents(self, application_number: str) -> GovApplicationStatus:
        return self._advance(application_number, "documents_verified")

    # -- DL test slots ---------------------------------------------------

    def list_dl_test_slots(self, rto_code: str) -> list[TestSlot]:
        base = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        slots = []
        for day in range(1, 8):
            for hour in (9, 11, 14):
                slot_id = f"{rto_code}-{day}-{hour}"
                capacity = self._slot_capacity.setdefault(slot_id, 5)
                if capacity > 0:
                    slots.append(
                        TestSlot(
                            slot_id=slot_id,
                            rto_code=rto_code,
                            starts_at=base + timedelta(days=day, hours=hour - base.hour),
                            capacity_left=capacity,
                        )
                    )
        return slots

    def book_dl_test(self, request: SlotBookingRequest) -> SlotBookingResult:
        status = self.get_application_status(request.application_number)
        if status.stage not in ("ll_issued", "dl_test_failed"):
            raise SarathiError(
                f"Cannot book a driving test while application is in stage '{status.stage}'"
            )
        capacity = self._slot_capacity.get(request.slot_id, 0)
        if capacity <= 0:
            raise SarathiError(f"Slot {request.slot_id} has no capacity left")
        self._slot_capacity[request.slot_id] = capacity - 1

        rto_code = request.slot_id.rsplit("-", 2)[0]
        slot = TestSlot(
            slot_id=request.slot_id,
            rto_code=rto_code,
            starts_at=datetime.now(UTC) + timedelta(days=1),
            capacity_left=capacity - 1,
        )
        booking = SlotBookingResult(
            booking_id=f"BK{next(self._booking_seq):07d}", slot=slot, confirmed=True
        )
        self._bookings[booking.booking_id] = booking
        self._advance(request.application_number, "dl_test_booked")
        return booking

    # -- Test results ----------------------------------------------------

    def report_test_result(self, report: TestResultReport) -> GovApplicationStatus:
        status = self.get_application_status(report.application_number)
        if report.test_type == "ll":
            if status.stage != "documents_verified":
                raise SarathiError(
                    f"LL test result not accepted in stage '{status.stage}'"
                )
            if report.passed:
                self._advance(report.application_number, "ll_test_passed")
                return self._advance(report.application_number, "ll_issued")
            return status
        if report.test_type == "dl":
            if status.stage != "dl_test_booked":
                raise SarathiError(
                    f"DL test result not accepted in stage '{status.stage}'"
                )
            if report.passed:
                self._advance(report.application_number, "dl_test_passed")
                return self._advance(report.application_number, "dl_issued")
            failed = self._advance(report.application_number, "dl_test_failed")
            failed = failed.model_copy(update={"failed_checkpoint": report.failed_checkpoint})
            self._applications[report.application_number] = failed
            return failed
        raise SarathiError(f"Unknown test type: {report.test_type}")

    # -- Internal ----------------------------------------------------------

    def _advance(self, application_number: str, stage: str) -> GovApplicationStatus:
        if stage not in GOV_STAGES:
            raise SarathiError(f"Unknown government stage: {stage}")
        current = self.get_application_status(application_number)
        updated = current.model_copy(
            update={"stage": stage, "updated_at": datetime.now(UTC)}
        )
        self._applications[application_number] = updated
        return updated


_client: SarathiClient | None = None


def get_client() -> SarathiClient:
    """The one place a real Sarathi client will ever be swapped in."""
    global _client
    if _client is None:
        _client = MockSarathiClient()
    return _client


def reset_client() -> None:
    """Test hook — discard mock state."""
    global _client
    _client = None
