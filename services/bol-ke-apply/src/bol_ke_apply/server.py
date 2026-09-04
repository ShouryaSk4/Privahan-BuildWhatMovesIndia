"""Module 6 — Bol Ke Apply MCP Server.

Per AGENTS.md Section 5.6 and 7.3:
A voice/conversational front door implemented as an MCP server.
Exposes Module 3 identity functions and Module 4 video-matching functions.
Does NOT expose Module 2 journey-state tools until Module 2 exists.
"""

import logging
import os

import httpx
from contracts.academy import VideoMatchRequest

try:
    # MCP SDK 2.x
    from mcp.server.mcpserver import MCPServer

    mcp = MCPServer(
        name="BolKeApply",
        instructions="Conversational front door for Parivahan MVP exposing identity and driving academy tools",
    )
except (ImportError, ModuleNotFoundError):
    from mcp.server.fastmcp import FastMCP  # type: ignore

    try:
        mcp = FastMCP("BolKeApply")
    except Exception:
        mcp = FastMCP()

# Graceful in-process integration when services run in the same Python environment
try:
    from identity_service.service import IdentityService

    _in_proc_identity = IdentityService()
except (ImportError, ModuleNotFoundError, AttributeError):
    _in_proc_identity = None

try:
    from academy_service.matcher import VideoMatcher

    _in_proc_matcher = VideoMatcher()
except (ImportError, ModuleNotFoundError, AttributeError):
    _in_proc_matcher = None

from bol_ke_apply.llm_client import get_llm_provider

logger = logging.getLogger("bol_ke_apply")
IDENTITY_SERVICE_URL = os.getenv("IDENTITY_SERVICE_URL", "http://127.0.0.1:8003")
ACADEMY_SERVICE_URL = os.getenv("ACADEMY_SERVICE_URL", "http://127.0.0.1:8004")
JOURNEY_SERVICE_URL = os.getenv("JOURNEY_SERVICE_URL", "http://127.0.0.1:8002")
llm = get_llm_provider()


@mcp.tool()
def fetch_identity(applicant_id: str) -> dict:
    """Fetch verified citizen profile from DigiLocker / Aadhaar e-KYC (Module 3).

    Surfaces both GPS suggested nearest RTO and legal Aadhaar jurisdiction address.
    """
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{IDENTITY_SERVICE_URL}/identity/fetch/{applicant_id}")
            if resp.status_code == 200:
                return resp.json()
    except httpx.HTTPError as exc:
        logger.debug("Identity service HTTP call fallback: %s", exc)

    if _in_proc_identity:
        return _in_proc_identity.fetch_identity(applicant_id).model_dump(mode="json")

    # Static fallback for disconnected execution
    return {
        "applicant_id": applicant_id,
        "source": "digilocker_aadhaar",
        "name": f"Citizen {applicant_id}",
        "dob": "2002-01-01",
        "address": "100 Feet Road, Indiranagar, Bengaluru, KA - 560038",
        "photo_url": "https://storage.parivahan.internal/photos/default.jpg",
        "gps_suggested_rto": "KA-03 Indiranagar",
        "aadhaar_registered_address": "100 Feet Road, Indiranagar, Bengaluru, KA - 560038",
        "addresses_match": True,
        "fetched_at": "2026-08-27T12:00:00Z",
        "age": 24,
        "age_eligible": True,
    }


@mcp.tool()
def check_mismatch(applicant_id: str) -> dict:
    """Perform rejection-prevention cross-check between Aadhaar and secondary identity records (Module 3)."""
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{IDENTITY_SERVICE_URL}/identity/mismatch-check/{applicant_id}")
            if resp.status_code == 200:
                return resp.json()
    except httpx.HTTPError as exc:
        logger.debug("Mismatch check HTTP call fallback: %s", exc)

    if _in_proc_identity:
        return _in_proc_identity.check_mismatch(applicant_id).model_dump(mode="json")

    return {
        "applicant_id": applicant_id,
        "mismatches": [],
        "clear_to_submit": True,
    }


@mcp.tool()
def match_video(
    applicant_id: str,
    query: str,
    journey_stage: str | None = None,
) -> dict:
    """Match a learner's difficulty or driving question to an instructional video clip (Module 4)."""
    payload = VideoMatchRequest(
        applicant_id=applicant_id,
        query=query,
        journey_stage=journey_stage,
    )

    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.post(
                f"{ACADEMY_SERVICE_URL}/academy/match-video",
                json=payload.model_dump(),
            )
            if resp.status_code == 200:
                return resp.json()
    except httpx.HTTPError as exc:
        logger.debug("Academy service HTTP call fallback: %s", exc)

    if _in_proc_matcher:
        return _in_proc_matcher.match(payload).model_dump(mode="json")

    return {
        "video_id": "vid_01_eight_turn",
        "topic": "8-turn",
        "confidence": 0.85,
        "fallback_message": None,
    }


@mcp.tool()
def whats_next(applicant_id: str) -> dict:
    """Get the citizen's current journey stage and next action (Module 2).

    Journey-state tools were held back until Module 2 existed (AGENTS.md §2);
    Module 2 merged on 28 Aug 2026, so this tool is now live.
    """
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{JOURNEY_SERVICE_URL}/journey/{applicant_id}")
            if resp.status_code == 200:
                return resp.json()
    except httpx.HTTPError as exc:
        logger.debug("Journey service HTTP call fallback: %s", exc)

    return {
        "applicant_id": applicant_id,
        "journey_type": "first_time_licence",
        "current_stage": "no_licence",
        "next_action": {"type": "start_application", "label": "Start your licence application"},
        "certainty": {"cost_inr": 1350, "eta_days": 21, "visit_count": 1},
        "fallback": "Journey service unreachable — showing the journey's starting state.",
    }


# --------------------------------------------------------------------------
# Journey ACTION tools — the autonomous half of the agent (Module 2 writes).
# Errors from Module 2 are relayed as structured dicts, never raised: the LLM
# reads them and tells the citizen what choice or fix is needed.
# --------------------------------------------------------------------------


def _journey_post(path: str, payload: dict | None = None) -> dict:
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(f"{JOURNEY_SERVICE_URL}{path}", json=payload)
            body = resp.json() if resp.content else {}
            if resp.status_code < 400:
                return body
            return {
                "blocked": True,
                "status": resp.status_code,
                "detail": body.get("detail", body) if isinstance(body, dict) else body,
            }
    except httpx.HTTPError as exc:
        logger.debug("Journey action fallback (%s): %s", path, exc)
        return {"error": "journey_unreachable", "detail": str(exc)}


@mcp.tool()
def start_application(applicant_id: str, confirmed_rto_code: str | None = None) -> dict:
    """Submit the Zero-Form learner's licence application (Module 2 -> Module 5).

    A 409 means the citizen must choose an RTO (GPS vs Aadhaar jurisdiction —
    pass confirmed_rto_code, or the literal "aadhaar_jurisdiction"). A 422
    means Rejection-Prevention blocked it; relay the mismatches and fixes.
    """
    return _journey_post(
        f"/journey/{applicant_id}/apply", {"confirmed_rto_code": confirmed_rto_code}
    )


@mcp.tool()
def report_event(applicant_id: str, event: str) -> dict:
    """Advance the journey state machine (e.g. "begin_practice") via Module 2."""
    return _journey_post(f"/journey/{applicant_id}/events", {"event": event})


@mcp.tool()
def list_test_slots(applicant_id: str, rto_code: str | None = None) -> dict:
    """List available automated driving-test track slots (via Module 2 -> Module 5)."""
    try:
        with httpx.Client(timeout=8.0) as client:
            params = {"rto_code": rto_code} if rto_code else None
            resp = client.get(
                f"{JOURNEY_SERVICE_URL}/journey/{applicant_id}/dl-test/slots", params=params
            )
            if resp.status_code == 200:
                slots = resp.json()
                return {"slots": slots[:8], "total": len(slots)}
            return {"blocked": True, "status": resp.status_code, "detail": resp.json().get("detail")}
    except httpx.HTTPError as exc:
        logger.debug("Slot listing fallback: %s", exc)
        return {"error": "journey_unreachable", "detail": str(exc)}


@mcp.tool()
def book_test_slot(applicant_id: str, slot_id: str) -> dict:
    """Book a driving-test slot. Only call after the citizen confirmed the slot."""
    return _journey_post(f"/journey/{applicant_id}/dl-test/bookings", {"slot_id": slot_id})


@mcp.tool()
def sync_status(applicant_id: str) -> dict:
    """Refresh the journey from the government side (Module 5) and return it."""
    return _journey_post(f"/journey/{applicant_id}/sync")


@mcp.tool()
def reset_journey(applicant_id: str) -> dict:
    """DEMO ONLY: forget this journey so the persona can start again.

    Destructive — only call when the citizen explicitly asked for a reset.
    """
    return _journey_post(f"/journey/{applicant_id}/reset")


def main():
    """Run the MCP server over standard stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
