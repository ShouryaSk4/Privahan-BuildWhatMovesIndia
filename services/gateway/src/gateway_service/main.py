"""Module 5 — Integration Gateway.

The only module allowed to talk to Sarathi / Vahan / eChallan (AGENTS.md §5.5).
Routes present the stable internal interface defined in contracts.gateway;
all government traffic goes through the SarathiClient swap point.
"""

from contracts.gateway import (
    GovApplicationStatus,
    GovSubmissionResult,
    LLApplicationSubmission,
    SlotBookingRequest,
    SlotBookingResult,
    TestResultReport,
    TestSlot,
)
from contracts.security import check_service_token, cors_origins
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .sarathi import SarathiClient, SarathiError, get_client


def require_service_token(x_service_token: str | None = Header(default=None)) -> None:
    """Gate the government surface to service-to-service callers only.

    Module 5 is the sole talker to Sarathi/Vahan (§5.5); a citizen's browser
    must never reach these endpoints. Only holders of the shared service token
    (i.e. Module 2) may call them.
    """
    if not check_service_token(x_service_token):
        raise HTTPException(status_code=401, detail="Service token required.")

app = FastAPI(
    title="Parivahan MVP — Integration Gateway (Module 5)",
    version="0.1.0",
    description="Stable internal interface to government systems. Mock-backed until real access exists.",
)

# The gateway is service-to-service only — no browser origin is allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Every /gov/* route requires the service token.
GOV = [Depends(require_service_token)]


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "module": "gateway"}


@app.post("/gov/ll-applications", response_model=GovSubmissionResult, dependencies=GOV)
def submit_ll_application(
    submission: LLApplicationSubmission, client: SarathiClient = Depends(get_client)
) -> GovSubmissionResult:
    return client.submit_ll_application(submission)


@app.get("/gov/applications/{application_number}", response_model=GovApplicationStatus, dependencies=GOV)
def get_application_status(
    application_number: str, client: SarathiClient = Depends(get_client)
) -> GovApplicationStatus:
    try:
        return client.get_application_status(application_number)
    except SarathiError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post(
    "/gov/applications/{application_number}/verify-documents",
    response_model=GovApplicationStatus,
    dependencies=GOV,
)
def verify_documents(
    application_number: str, client: SarathiClient = Depends(get_client)
) -> GovApplicationStatus:
    """Mock RTO-side document verification.

    With real Sarathi access this becomes an inbound status we poll or receive;
    the mock exposes it as an action so the journey can be exercised end to end.
    """
    try:
        return client.verify_documents(application_number)
    except SarathiError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/gov/dl-test/slots", response_model=list[TestSlot], dependencies=GOV)
def list_dl_test_slots(
    rto_code: str, client: SarathiClient = Depends(get_client)
) -> list[TestSlot]:
    return client.list_dl_test_slots(rto_code)


@app.post("/gov/dl-test/bookings", response_model=SlotBookingResult, dependencies=GOV)
def book_dl_test(
    request: SlotBookingRequest, client: SarathiClient = Depends(get_client)
) -> SlotBookingResult:
    try:
        return client.book_dl_test(request)
    except SarathiError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/gov/test-results", response_model=GovApplicationStatus, dependencies=GOV)
def report_test_result(
    report: TestResultReport, client: SarathiClient = Depends(get_client)
) -> GovApplicationStatus:
    """Record an LL or DL test outcome (mock stand-in for the RTO reporting it)."""
    try:
        return client.report_test_result(report)
    except SarathiError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
