"""Module 2 → Module 5 client.

Hard rule (AGENTS.md §5.5): no module other than the gateway talks to
Sarathi / Vahan / eChallan. Module 2 therefore speaks only this client,
which speaks only the gateway's stable internal interface.
"""

from __future__ import annotations

import os

import httpx
from contracts.gateway import (
    GovApplicationStatus,
    GovSubmissionResult,
    LLApplicationSubmission,
    SlotBookingRequest,
    SlotBookingResult,
    TestSlot,
)


class GatewayUnavailable(Exception):
    pass


class GatewayRejection(Exception):
    """The government side refused the request; carries its human-readable detail."""


class GatewayClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("GATEWAY_URL", "http://localhost:8005")).rstrip("/")

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            res = httpx.request(method, f"{self.base_url}{path}", timeout=10, **kwargs)
        except httpx.HTTPError as exc:
            raise GatewayUnavailable(
                f"Integration Gateway unreachable at {self.base_url}: {exc}"
            ) from exc
        return res

    def submit_ll_application(self, submission: LLApplicationSubmission) -> GovSubmissionResult:
        res = self._request("POST", "/gov/ll-applications", json=submission.model_dump())
        res.raise_for_status()
        return GovSubmissionResult.model_validate(res.json())

    def get_application_status(self, application_number: str) -> GovApplicationStatus:
        res = self._request("GET", f"/gov/applications/{application_number}")
        res.raise_for_status()
        return GovApplicationStatus.model_validate(res.json())

    def list_dl_test_slots(self, rto_code: str) -> list[TestSlot]:
        res = self._request("GET", "/gov/dl-test/slots", params={"rto_code": rto_code})
        res.raise_for_status()
        return [TestSlot.model_validate(s) for s in res.json()]

    def book_dl_test(self, request: SlotBookingRequest) -> SlotBookingResult:
        res = self._request("POST", "/gov/dl-test/bookings", json=request.model_dump())
        if res.status_code == 409:
            raise GatewayRejection(res.json().get("detail", "Booking refused by the RTO system."))
        res.raise_for_status()
        return SlotBookingResult.model_validate(res.json())

    def verify_documents(self, application_number: str) -> None:
        try:
            res = self._request("POST", f"/gov/applications/{application_number}/verify-documents")
            res.raise_for_status()
        except Exception:
            pass


def get_gateway_client() -> GatewayClient:
    return GatewayClient()
