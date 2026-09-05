"""Module 2 → Module 5 client.

Hard rule (AGENTS.md §5.5): no module other than the gateway talks to
Sarathi / Vahan / eChallan. Module 2 therefore speaks only this client,
which speaks only the gateway's stable internal interface.
"""

from __future__ import annotations

import logging
import os

import httpx
from contracts.gateway import (
    GovApplicationStatus,
    GovSubmissionResult,
    LLApplicationSubmission,
    SlotBookingRequest,
    SlotBookingResult,
    TestResultReport,
    TestSlot,
)
from contracts.security import service_token

logger = logging.getLogger("journey.gateway")


class GatewayUnavailable(Exception):
    pass


class GatewayRejection(Exception):
    """The government side refused the request; carries its human-readable detail."""


class GatewayClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("GATEWAY_URL", "http://localhost:8005")).rstrip("/")

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        headers = {**kwargs.pop("headers", {}), "X-Service-Token": service_token()}
        try:
            res = httpx.request(
                method,
                f"{self.base_url}{path}",
                timeout=10,
                follow_redirects=True,
                headers=headers,
                **kwargs,
            )
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
        # Best-effort: verification is re-driven by sync if it fails here.
        try:
            res = self._request("POST", f"/gov/applications/{application_number}/verify-documents")
            res.raise_for_status()
        except (GatewayUnavailable, httpx.HTTPError) as exc:
            logger.debug("verify_documents best-effort failed: %s", exc)

    def report_test_result(self, report: TestResultReport) -> GovApplicationStatus:
        res = self._request("POST", "/gov/test-results", json=report.model_dump())
        if res.status_code == 409:
            raise GatewayRejection(res.json().get("detail", "Result refused by the RTO system."))
        res.raise_for_status()
        return GovApplicationStatus.model_validate(res.json())


class DirectGatewayClient:
    """Direct in-memory gateway client for serverless/monolithic execution."""

    def __init__(self) -> None:
        from gateway_service.sarathi import get_client
        self._client = get_client()

    def submit_ll_application(self, submission: LLApplicationSubmission) -> GovSubmissionResult:
        return self._client.submit_ll_application(submission)

    def get_application_status(self, application_number: str) -> GovApplicationStatus:
        from gateway_service.sarathi import SarathiError
        try:
            return self._client.get_application_status(application_number)
        except SarathiError as exc:
            raise GatewayRejection(str(exc)) from exc

    def list_dl_test_slots(self, rto_code: str) -> list[TestSlot]:
        return self._client.list_dl_test_slots(rto_code)

    def book_dl_test(self, request: SlotBookingRequest) -> SlotBookingResult:
        from gateway_service.sarathi import SarathiError
        try:
            return self._client.book_dl_test(request)
        except SarathiError as exc:
            raise GatewayRejection(str(exc)) from exc

    def verify_documents(self, application_number: str) -> None:
        from gateway_service.sarathi import SarathiError
        try:
            self._client.verify_documents(application_number)
        except SarathiError as exc:
            logger.debug("verify_documents best-effort failed: %s", exc)

    def report_test_result(self, report: TestResultReport) -> GovApplicationStatus:
        from gateway_service.sarathi import SarathiError
        try:
            return self._client.report_test_result(report)
        except SarathiError as exc:
            raise GatewayRejection(str(exc)) from exc


def get_gateway_client() -> GatewayClient | DirectGatewayClient:
    mode = os.environ.get("GATEWAY_MODE", "").lower()
    if mode == "direct" or os.environ.get("VERCEL") or os.environ.get("VERCEL_URL"):
        try:
            return DirectGatewayClient()
        except ImportError:
            pass
    return GatewayClient()
