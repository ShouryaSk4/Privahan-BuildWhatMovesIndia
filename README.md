# Parivahan MVP — Build What Moves India

A citizen-experience and orchestration layer that sits on top of the existing **Sarathi / Vahan / eChallan** infrastructure.

The MVP proves exactly one journey end to end:
> **First-time car licence**  
> "I want to get my first licence" → application → learner's licence (LL) → 30-day practice window → driving test (DL) → licence in hand.

The core ideas:
1. **Zero-Form Licence** — form-free application using verified identity data (DigiLocker / Aadhaar e-KYC).
2. **Driving Academy** — AI-assisted 30-day practice window with curated video matching.
3. **Bol Ke Apply** — voice/conversational front door implemented as an MCP server.

---

## Module Matrix & Ownership

This repository is built concurrently by two developers in the same repository:

| Module | Title | Path | Owner | Tech Stack | Status |
|---|---|---|---|---|---|
| **Module 3** | **Identity & Document Service** | `services/identity` | **You** | Python, FastAPI | **Active — In Development** |
| **Module 4** | **Driving Academy Assistant** | `services/academy` | **You** | Python, FastAPI, LLM | **Active — In Development** |
| **Module 6** | **Bol Ke Apply** | `services/bol-ke-apply` | **You** | Python, MCP SDK, LLM | **Active — In Development** |
| **Module 1** | **Citizen Experience** | `apps/web` | Collaborator | React, TypeScript, Vite | Reserved / Deferred |
| **Module 2** | **Journey & Requirements Engine** | `services/journey` | Collaborator | Python, FastAPI | Reserved / Deferred |
| **Module 5** | **Integration Gateway** | `services/gateway` | Collaborator | Python, FastAPI (Mock) | Reserved / Deferred |

Shared Single Source of Truth:
- `packages/contracts`: Shared Pydantic models consumed by all backend services and used to generate frontend TypeScript types via OpenAPI.

---

## Repository Structure

```text
.
├── apps/
│   └── web/                   # Module 1: Citizen Experience (React/Vite frontend) [Collaborator]
├── packages/
│   └── contracts/             # Shared Pydantic models (Single Source of Truth)
│       └── contracts/
│           ├── identity.py    # VerifiedProfile, Mismatch, MismatchCheckResult
│           ├── academy.py     # VideoMatchRequest, VideoMatchResult, AcademyVideo
│           ├── enums.py       # JourneyStage, IdentitySource
│           └── mcp_tools.py   # MCP Tool declarations
├── services/
│   ├── identity/              # Module 3: Zero-Form Identity Service [You]
│   ├── academy/               # Module 4: Driving Academy Assistant [You]
│   ├── bol-ke-apply/          # Module 6: Bol Ke Apply MCP Server [You]
│   ├── journey/               # Module 2: Journey & Requirements Engine [Collaborator]
│   └── gateway/               # Module 5: Integration Gateway (Sarathi/Vahan Mock) [Collaborator]
├── pyproject.toml             # uv workspace root definition
├── .python-version            # Python 3.13
└── AGENTS.md                  # System architecture and engineering guidelines
```

---

## Quickstart

### Prerequisites
- [uv](https://docs.astral.sh/uv/) (installed)
- Python >= 3.11 (3.13 recommended)

### 1. Install & Sync Dependencies
```powershell
uv sync
```

### 2. Run All Tests
```powershell
uv run pytest
```

### 3. Run Lint Checks
```powershell
uv run ruff check .
```

---

## Running Services Independently

Each module is self-contained and runnable independently:

### Module 3 — Identity Service
```powershell
uv run --package identity-service uvicorn identity_service.main:app --reload --port 8003
```
- API Docs: `http://localhost:8003/docs`

### Module 4 — Academy Assistant
```powershell
uv run --package academy-service uvicorn academy_service.main:app --reload --port 8004
```
- API Docs: `http://localhost:8004/docs`

### Module 6 — Bol Ke Apply (MCP Server)
```powershell
uv run --package bol-ke-apply python -m bol_ke_apply.server
```

---

## Working Agreements (from AGENTS.md)
1. **Contracts are Additive-Only**: Do not rename or delete existing fields in `packages/contracts`. Add fields if needed.
2. **Module Boundaries**: Do not touch another module's directory under `services/`.
3. **External Dependencies are Mocked**: DigiLocker, UIDAI, and Sarathi are mocked locally so development never blocks on external access.
4. **GPS vs Aadhaar Address**: GPS location suggests the nearest RTO; Aadhaar registered address determines RTO jurisdiction. These are distinct and never silently conflated.
