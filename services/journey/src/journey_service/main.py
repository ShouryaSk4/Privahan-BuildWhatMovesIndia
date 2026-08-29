"""Module 2 — Journey & Requirements Engine.

The backend brain (AGENTS.md §5.2): owns the journey state machine, determines
required documents/steps, produces cost/timeline/visit-count (the informational
half of the Certainty Contract), integrates Module 3's verified data, and talks
to government systems only through Module 5.
"""

from contracts.gateway import LLApplicationSubmission, SlotBookingRequest, TestSlot
from contracts.identity import Mismatch, MismatchCheckResult, VerifiedProfile
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
from .clients.identity import IdentityClient, IdentityUnavailable, get_identity_client
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


# Mismatch fields that describe *jurisdiction*, not bad identity data. These are
# surfaced for the citizen to resolve (§5.3) instead of blocking the application.
ADVISORY_MISMATCH_FIELDS = frozenset({"aadhaar_registered_address"})


def is_advisory(m: Mismatch) -> bool:
    """Module 3 now grades mismatches (severity: "error" blocks, "warning" advises).

    Prefer that grading; the field-based rule remains as a fallback for older
    payloads where severity defaults to "error" on jurisdiction entries.
    """
    return m.severity == "warning" or m.field in ADVISORY_MISMATCH_FIELDS

# Sentinel the citizen sends to mean "file it at my Aadhaar jurisdiction RTO".
# VerifiedProfile carries the Aadhaar *address* but not its RTO code, so Module 2
# derives a state code from the address. When Module 3 exposes the jurisdiction
# RTO directly, resolve from that field instead and drop the derivation.
AADHAAR_JURISDICTION_CHOICE = "aadhaar_jurisdiction"
DEFAULT_RTO_CODE = "DL01"


def resolve_rto_code(profile: VerifiedProfile, confirmed: str | None) -> str:
    """Turn the citizen's confirmed choice into the RTO code sent to Module 5."""
    if confirmed is None:
        return profile.gps_suggested_rto or DEFAULT_RTO_CODE
    if confirmed != AADHAAR_JURISDICTION_CHOICE:
        return confirmed
    address = profile.aadhaar_registered_address or ""
    # Addresses end like "... , UP - 226010"; take the two-letter state token.
    for token in reversed([t.strip() for t in address.replace("-", ",").split(",")]):
        if len(token) == 2 and token.isalpha():
            return token.upper()
    return profile.gps_suggested_rto or DEFAULT_RTO_CODE


class EventRequest(BaseModel):
    event: str


class ApplyRequest(BaseModel):
    # Required only when Module 3 reports the GPS RTO and the Aadhaar-address
    # jurisdiction disagree: the disagreement is surfaced, the citizen chooses.
    confirmed_rto_code: str | None = None


class VerifiedIdentityView(BaseModel):
    profile: VerifiedProfile
    mismatch_check: MismatchCheckResult
    # Module 2 owns the advisory-vs-blocking rule so Module 1 never re-implements it.
    blocking_mismatches: list[Mismatch] = []
    advisory_mismatches: list[Mismatch] = []
    clear_to_submit: bool = True
    # The two RTO choices to offer when jurisdiction and location disagree (§5.3).
    gps_rto_choice: str | None = None
    aadhaar_rto_choice: str | None = None


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
    try:
        profile = identity.fetch_identity(applicant_id)
        mismatch = identity.check_mismatch(applicant_id)
    except IdentityUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    advisory = [m for m in mismatch.mismatches if is_advisory(m)]
    blocking = [m for m in mismatch.mismatches if not is_advisory(m)]
    return VerifiedIdentityView(
        profile=profile,
        mismatch_check=mismatch,
        blocking_mismatches=blocking,
        advisory_mismatches=advisory,
        clear_to_submit=not blocking,
        gps_rto_choice=profile.gps_suggested_rto,
        aadhaar_rto_choice=(
            AADHAAR_JURISDICTION_CHOICE if profile.addresses_match is False else None
        ),
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
    if record.stage != JourneyStage.NO_LICENCE:
        raise HTTPException(status_code=409, detail="An application already exists for this journey.")

    try:
        profile = identity.fetch_identity(applicant_id)
        mismatch = identity.check_mismatch(applicant_id)
    except IdentityUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Module 3 reports the RTO-jurisdiction disagreement as a mismatch entry, which
    # clears `clear_to_submit`. But §5.3 requires that disagreement to be *surfaced*
    # for the citizen to resolve, not to block the application — students and recent
    # movers legitimately hit it. So split the two kinds:
    #   blocking  — identity data that will not clear the RTO's checks (name, DOB…)
    #   advisory  — jurisdiction, resolved by the citizen confirming an RTO below
    blocking = [m for m in mismatch.mismatches if not is_advisory(m)]
    if blocking:
        raise HTTPException(
            status_code=422,
            detail={
                "reason": "rejection_prevention",
                "message": "Submission blocked: fetched records would not clear the RTO's own checks.",
                "mismatches": [m.model_dump() for m in blocking],
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
    rto_code = resolve_rto_code(profile, body.confirmed_rto_code)

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

    engine.set_application_number(applicant_id, result.application_number)
    engine.apply_event(applicant_id, "ll_application_submitted")
    return engine.state(applicant_id)


@app.post("/journey/{applicant_id}/reset", response_model=JourneyState)
def reset_journey(
    applicant_id: str, engine: JourneyEngine = Depends(get_engine)
) -> JourneyState:
    """Demo reset: forget this journey so the persona can be walked again.

    Demo personas are shared records; without this, one visitor completing a
    journey consumes the persona for everyone until a restart.
    """
    engine.reset_applicant(applicant_id)
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
        if record.stage == JourneyStage.DL_TEST_RESULT_FAIL
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
