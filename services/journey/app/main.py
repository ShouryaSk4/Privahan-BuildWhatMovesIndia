"""Module 2 — Journey & Requirements Engine.

The backend brain (AGENTS.md §5.2): owns the journey state machine, determines
required documents/steps, produces cost/timeline/visit-count (the informational
half of the Certainty Contract), integrates Module 3's verified data, and talks
to government systems only through Module 5.
"""

from contracts.gateway import LLApplicationSubmission, SlotBookingRequest, TestSlot
from contracts.identity import MismatchCheckResult, VerifiedProfile
from contracts.journey import JourneyStage, JourneyState
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .clients.gateway import (
    GatewayClient,
    GatewayRejection,
    GatewayUnavailable,
    get_gateway_client,
)
from .clients.identity import IdentityClient, get_identity_client
from .engine import GateError, JourneyEngine, TransitionError, get_engine

app = FastAPI(
    title="Parivahan MVP — Journey & Requirements Engine (Module 2)",
    version="0.1.0",
    description="Owns the journey state machine; replaces self-declared licence status.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # internal service; tighten when deployed
    allow_methods=["*"],
    allow_headers=["*"],
)


class EventRequest(BaseModel):
    event: str


class ApplyRequest(BaseModel):
    # Required only when Module 3 reports the GPS RTO and the Aadhaar-address
    # jurisdiction disagree: the disagreement is surfaced, the citizen chooses.
    confirmed_rto_code: str | None = None


class VerifiedIdentityView(BaseModel):
    profile: VerifiedProfile
    mismatch_check: MismatchCheckResult


class BookingRequest(BaseModel):
    slot_id: str


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "module": "journey"}


@app.get("/journey/{applicant_id}", response_model=JourneyState)
def get_journey(applicant_id: str, engine: JourneyEngine = Depends(get_engine)) -> JourneyState:
    """What's next — the AGENTS.md §7.4 response."""
    return engine.state(applicant_id)


@app.post("/journey/{applicant_id}/events", response_model=JourneyState)
def report_event(
    applicant_id: str, body: EventRequest, engine: JourneyEngine = Depends(get_engine)
) -> JourneyState:
    try:
        engine.apply_event(applicant_id, body.event)
    except (TransitionError, GateError) as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    return engine.state(applicant_id)


@app.get("/journey/{applicant_id}/verified-profile", response_model=VerifiedIdentityView)
def verified_profile(
    applicant_id: str, identity: IdentityClient = Depends(get_identity_client)
) -> VerifiedIdentityView:
    """Module 2's integrated view of Module 3: what is already verified."""
    return VerifiedIdentityView(
        profile=identity.fetch_identity(applicant_id),
        mismatch_check=identity.check_mismatch(applicant_id),
    )


@app.post("/journey/{applicant_id}/apply", response_model=JourneyState)
def apply(
    applicant_id: str,
    body: ApplyRequest,
    engine: JourneyEngine = Depends(get_engine),
    identity: IdentityClient = Depends(get_identity_client),
    gateway: GatewayClient = Depends(get_gateway_client),
) -> JourneyState:
    """Zero-form application: verified identity in, LL application out."""
    record = engine.record(applicant_id)
    if record.stage != JourneyStage.no_licence:
        raise HTTPException(status_code=409, detail="An application already exists for this journey.")

    profile = identity.fetch_identity(applicant_id)
    mismatch = identity.check_mismatch(applicant_id)
    if not mismatch.clear_to_submit:
        raise HTTPException(
            status_code=422,
            detail={
                "reason": "rejection_prevention",
                "message": "Submission blocked: fetched records would not clear the RTO's own checks.",
                "mismatches": [m.model_dump() for m in mismatch.mismatches],
            },
        )

    # Jurisdiction comes from the Aadhaar-registered address; the GPS location
    # only ever suggests a convenient RTO. If they disagree, surface it (§5.3).
    if profile.addresses_match is False and body.confirmed_rto_code is None:
        raise HTTPException(
            status_code=409,
            detail={
                "reason": "rto_confirmation_required",
                "message": (
                    "Your Aadhaar-registered address and current location point to different "
                    "RTOs. Confirm which RTO should receive the application."
                ),
                "gps_suggested_rto": profile.gps_suggested_rto,
                "aadhaar_registered_address": profile.aadhaar_registered_address,
            },
        )
    rto_code = body.confirmed_rto_code or "DL01"

    try:
        result = gateway.submit_ll_application(
            LLApplicationSubmission(
                applicant_id=applicant_id,
                name=profile.name,
                dob=profile.dob.isoformat(),
                address=profile.address,
                photo_url=profile.photo_url,
                rto_code=rto_code,
                vehicle_class="LMV",
            )
        )
    except GatewayUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    record.application_number = result.application_number
    engine.apply_event(applicant_id, "ll_application_submitted")
    return engine.state(applicant_id)


@app.post("/journey/{applicant_id}/sync", response_model=JourneyState)
def sync(
    applicant_id: str,
    engine: JourneyEngine = Depends(get_engine),
    gateway: GatewayClient = Depends(get_gateway_client),
) -> JourneyState:
    """Poll the government side (through Module 5) and fold its status in."""
    record = engine.record(applicant_id)
    if record.application_number is None:
        return engine.state(applicant_id)
    try:
        status = gateway.get_application_status(record.application_number)
    except GatewayUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    engine.sync_from_gov(applicant_id, status.stage, status.failed_checkpoint)
    return engine.state(applicant_id)


@app.get("/journey/{applicant_id}/dl-test/slots", response_model=list[TestSlot])
def dl_test_slots(
    applicant_id: str,
    rto_code: str = "DL01",
    gateway: GatewayClient = Depends(get_gateway_client),
) -> list[TestSlot]:
    try:
        return gateway.list_dl_test_slots(rto_code)
    except GatewayUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/journey/{applicant_id}/dl-test/bookings", response_model=JourneyState)
def book_dl_test(
    applicant_id: str,
    body: BookingRequest,
    engine: JourneyEngine = Depends(get_engine),
    gateway: GatewayClient = Depends(get_gateway_client),
) -> JourneyState:
    record = engine.record(applicant_id)
    if record.application_number is None:
        raise HTTPException(status_code=409, detail="No application on file for this journey.")
    event = (
        "dl_test_rebooked"
        if record.stage == JourneyStage.dl_test_result_fail
        else "dl_test_booked"
    )
    # Enforce rule gates (practice window / retest wait) before touching the gateway.
    try:
        engine.check_gate(record, event)
    except GateError as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    try:
        gateway.book_dl_test(
            SlotBookingRequest(
                applicant_id=applicant_id,
                application_number=record.application_number,
                slot_id=body.slot_id,
            )
        )
    except GatewayUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GatewayRejection as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    try:
        engine.apply_event(applicant_id, event)
    except (TransitionError, GateError) as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    return engine.state(applicant_id)
