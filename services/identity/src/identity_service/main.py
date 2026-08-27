"""FastAPI entrypoint for Module 3 (Identity & Document Service)."""

from contracts.identity import MismatchCheckResult, VerifiedProfile
from fastapi import FastAPI, HTTPException, Query

from identity_service.service import IdentityService

app = FastAPI(
    title="Parivahan Identity Service",
    version="0.1.0",
    description="Module 3: Zero-Form Identity & Document Service with DigiLocker / Aadhaar e-KYC pull and rejection prevention.",
)

service = IdentityService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "identity-service"}


@app.get("/identity/personas", response_model=list[str])
def list_personas() -> list[str]:
    """List available mock citizen personas for testing."""
    return service.list_personas()


@app.get("/identity/fetch/{applicant_id}", response_model=VerifiedProfile)
def fetch_identity(
    applicant_id: str,
    gps_suggested_rto: str | None = Query(
        default=None,
        description="Optional GPS/device location suggested nearest RTO",
    ),
) -> VerifiedProfile:
    """Fetch verified profile from DigiLocker / Aadhaar e-KYC."""
    try:
        return service.fetch_identity(
            applicant_id=applicant_id,
            gps_suggested_rto=gps_suggested_rto,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/identity/mismatch-check/{applicant_id}", response_model=MismatchCheckResult)
def check_mismatch(applicant_id: str) -> MismatchCheckResult:
    """Check for data discrepancies and rejection prevention before submission."""
    try:
        return service.check_mismatch(applicant_id=applicant_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("identity_service.main:app", host="127.0.0.1", port=8003, reload=True)
