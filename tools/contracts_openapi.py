"""Emit an OpenAPI document for shared contracts that have no local service yet
(Modules 3 and 4 are built in separate silos).

The routes below are the provisional HTTP shapes Modules 3/4 are expected to
expose (mirroring the §7.3 tool names 1:1); they exist here only so
openapi-typescript can generate frontend types from the same Pydantic source
of truth — no hand-written TypeScript duplicates (AGENTS.md §4.3).
"""

import json

from fastapi import FastAPI

from contracts.academy import VideoMatchRequest, VideoMatchResult
from contracts.identity import MismatchCheckResult, VerifiedProfile

app = FastAPI(title="Parivahan shared contracts (silo modules)", version="0.1.0")


@app.get("/identity/{applicant_id}", response_model=VerifiedProfile, tags=["module-3"])
def fetch_identity(applicant_id: str):  # pragma: no cover - schema only
    raise NotImplementedError


@app.get(
    "/identity/{applicant_id}/mismatches",
    response_model=MismatchCheckResult,
    tags=["module-3"],
)
def check_mismatch(applicant_id: str):  # pragma: no cover - schema only
    raise NotImplementedError


@app.post("/match", response_model=VideoMatchResult, tags=["module-4"])
def match_video(request: VideoMatchRequest):  # pragma: no cover - schema only
    raise NotImplementedError


if __name__ == "__main__":
    print(json.dumps(app.openapi(), indent=2))
