# Module 3 — Identity & Document Service

Owner: **You**  
Status: **Active — Ready to Build**

## Overview
The Zero-Form Licence engine. It pulls identity and address details via DigiLocker / Aadhaar e-KYC, cross-verifies PAN records, checks for rejection risks before submission, and preserves the distinction between device GPS location and legal Aadhaar jurisdiction.

## Responsibilities
- DigiLocker / Aadhaar e-KYC pull (name, DOB, address, photo).
- PAN fallback & cross-validation.
- Rejection-prevention mismatch checks.
- Disagreement surfacing: GPS location (nearest RTO) vs Aadhaar registered address (RTO jurisdiction).

## Running Independently
From the repository root:
```powershell
uv run --package identity-service uvicorn identity_service.main:app --reload --port 8003
```
- Interactive Swagger UI: `http://localhost:8003/docs`
- OpenAPI JSON: `http://localhost:8003/openapi.json`

## Testing
```powershell
uv run pytest services/identity
```
