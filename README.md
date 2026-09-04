# Parivahan MVP — Build What Moves India

A citizen-experience and orchestration layer that sits on top of the existing **Sarathi / Vahan / eChallan** infrastructure — not a replacement for it.

The MVP proves exactly one journey end to end:
> **First-time car licence**
> "I want to get my first licence" → application → learner's licence (LL) → 30-day practice window → driving test (DL) → licence in hand.

The core ideas:
1. **Zero-Form Licence** — form-free application using verified identity data (DigiLocker / Aadhaar e-KYC).
2. **Driving Academy** — AI-assisted 30-day practice window with curated video matching.
3. **Bol Ke Apply** — voice/conversational front door implemented as an MCP server.

---

## Module Matrix & Status

**All six modules are now merged** (28 Aug 2026). Modules 3/4/6 and Modules 1/2/5 were built
in parallel silos against the shared contracts in `packages/contracts`, then integrated.

| Module | Title | Path | Tech Stack | Status |
|---|---|---|---|---|
| **Module 1** | Citizen Experience | `apps/web` | React, TypeScript, Vite | ✅ Merged |
| **Module 2** | Journey & Requirements Engine | `services/journey` | Python, FastAPI | ✅ Merged |
| **Module 3** | Identity & Document Service | `services/identity` | Python, FastAPI | ✅ Merged |
| **Module 4** | Driving Academy Assistant | `services/academy` | Python, FastAPI, LLM | ✅ Merged |
| **Module 5** | Integration Gateway | `services/gateway` | Python, FastAPI (Mock) | ✅ Merged |
| **Module 6** | Bol Ke Apply | `services/bol-ke-apply` | Python, MCP SDK, LLM | ✅ Merged |

Shared Single Source of Truth:
- `packages/contracts`: Pydantic models consumed by all backend services and used to generate
  frontend TypeScript types via OpenAPI. **Never hand-write a duplicate of a shared shape.**

---

## Repository Structure

```text
.
├── apps/
│   └── web/                   # Module 1: Citizen Experience (React/Vite)
├── packages/
│   └── contracts/             # Shared Pydantic models (Single Source of Truth)
│       └── contracts/
│           ├── identity.py    # VerifiedProfile, Mismatch, MismatchCheckResult
│           ├── academy.py     # VideoMatchRequest, VideoMatchResult, AcademyVideo
│           ├── journey.py     # JourneyState, NextAction, Certainty, RequiredDocument
│           ├── gateway.py     # LLApplicationSubmission, TestSlot, GovApplicationStatus…
│           ├── enums.py       # JourneyStage, IdentitySource
│           └── mcp_tools.py   # MCP Tool declarations
├── services/
│   ├── identity/              # Module 3: Zero-Form Identity Service
│   ├── academy/               # Module 4: Driving Academy Assistant
│   ├── bol-ke-apply/          # Module 6: Bol Ke Apply MCP Server
│   ├── journey/               # Module 2: Journey & Requirements Engine
│   └── gateway/               # Module 5: Integration Gateway (Sarathi/Vahan mock)
├── tools/                     # OpenAPI → TypeScript type generation (§4.3 / §8.5)
├── pyproject.toml             # uv workspace root
└── AGENTS.md                  # System architecture and engineering guidelines
```

---

## Service map

| Module | Port | Base URL | Key endpoints |
|---|---|---|---|
| Journey (M2) | 8002 | http://localhost:8002 | `GET /journey/{id}`, `POST /journey/{id}/apply`, `POST /journey/{id}/sync` |
| Identity (M3) | 8003 | http://localhost:8003 | `GET /identity/fetch/{id}`, `GET /identity/mismatch-check/{id}` |
| Academy (M4) | 8004 | http://localhost:8004 | `POST /academy/match-video`, `GET /academy/videos` |
| Gateway (M5) | 8005 | http://localhost:8005 | `POST /gov/ll-applications`, `GET /gov/dl-test/slots` |
| Web (M1) | 5173 | http://localhost:5173 | — |
| Bol Ke Apply (M6) | 8006 | http://localhost:8006 | `POST /chat`, `POST /transcribe`, `GET /tools`, `POST /tools/whats_next` (plus MCP over stdio) |

---

## Quickstart

Prereqs: [uv](https://docs.astral.sh/uv/), Python ≥3.11 (3.13 recommended), Node 20+, pnpm.

```bash
uv sync              # all Python workspace members
pnpm install         # web app
```

### Run the full stack (5 terminals, or use the ports above)

```bash
# Module 3 — Identity
uv run --package identity-service uvicorn identity_service.main:app --port 8003

# Module 4 — Academy
uv run --package academy-service uvicorn academy_service.main:app --port 8004

# Module 5 — Integration Gateway (mock government side)
uv run --package parivahan-gateway uvicorn app.main:app --port 8005

# Module 2 — Journey Engine (IDENTITY_MODE=http uses the real Module 3)
IDENTITY_MODE=http JOURNEY_FAST_FORWARD=1 uv run --package parivahan-journey uvicorn app.main:app --port 8002

# Module 1 — Web
pnpm --dir apps/web dev
```

`JOURNEY_FAST_FORWARD=1` collapses the 30-day practice and 7-day retest waits so the whole
journey is demoable in minutes. Leave it unset to enforce the real waiting periods.

### Module 6 — Bol Ke Apply

```bash
# HTTP agent (the web app's voice modal talks to this), port 8006
uv run uvicorn bol_ke_apply.api:app --port 8006

# or the MCP server over stdio
uv run --package bol-ke-apply python -m bol_ke_apply.server
```

**LLM provider (OpenAI preferred).** Set `OPENAI_API_KEY` in `.env` and the agent
upgrades from keyword routing to **native function calling** on `gpt-4o-mini`:
the model reads the citizen's message (Hindi / Hinglish / English, any phrasing),
chooses among the platform tools — `fetch_identity`, `check_mismatch`,
`match_video`, `whats_next` — executes them, and answers from the results with
short per-applicant conversation memory. Tool schemas are generated from the
Pydantic contracts in `packages/contracts/contracts/mcp_tools.py`, so they can
never drift from the platform. Replies also carry real synthesized speech
(`audio_url`, `gpt-4o-mini-tts`) and `/transcribe` does server-side
speech-to-text (`gpt-4o-transcribe`) for browsers with weak speech support.
Inbound text passes the free `omni-moderation-latest` gate.

The fallback chain never leaves the assistant dead:
**OpenAI tool-calling → Gemini phrased replies → offline keyword routing (mock).**
Provider selection: `BOL_KE_APPLY_LLM_PROVIDER` = `openai` | `gemini` | `mock` |
`auto` (auto picks by available API key). Live routing evals live in
`services/bol-ke-apply/tests/test_openai_agent.py` and run only when
`OPENAI_API_KEY` is present.

## Tests & lint

```bash
uv run pytest                                   # contracts + identity + academy + bol-ke-apply
cd services/journey && uv run pytest            # Module 2
cd services/gateway && uv run pytest            # Module 5
pnpm --dir apps/web test                        # Module 1
pnpm --dir apps/web exec tsc -b                 # type check
uv run ruff check .
```

## Type generation (AGENTS.md §4.3 / §8.5)

Pydantic → FastAPI → OpenAPI → `openapi-typescript` → `apps/web/src/api/types/*`.

```bash
bash tools/gen-types.sh
```

Re-run after any contract or endpoint change. The script pulls schemas from the **real**
identity and academy services, so no hand-written duplicate types exist anywhere.

---

## The 3-minute demo script

Start the full stack, open the web app, then:

1. **The promise** *(15s)* — landing page. Point at the savings strip: an agent charges
   ₹3,500–5,000 in cash with no receipt; this journey is ₹1,350, promised upfront with cost,
   days, and visit count. "We sell what the tout sells: certainty."
2. **Zero forms** *(40s)* — continue as `applicant_001` → "Fetch my details & start". The
   review screen says *Fields you typed: 0* — every value came from Module 3's e-KYC pull.
   Tick, submit; an application number exists.
3. **The test comes home** *(40s)* — open the RTO simulator (dev panel), click "RTO verifies
   documents". The learner's test appears **in the app**: answer the 3 road-rules questions,
   pass, and the learner's licence is issued — no RTO visit.
4. **The coach** *(45s)* — start the practice window, book a slot, then in the simulator fail
   the driving test at *reverse parking*. The rail shows "Retry", the missed checkpoint is
   named, and the Driving Academy opens pre-loaded with the right lesson from Module 4's
   real catalog. "Failure becomes a plan, not a fine."
5. **The ending** *(20s)* — rebook, pass. Confetti, and the driving licence rendered as a card
   built from the same verified data: *zero forms, one visit, a coach the whole way.*

**Two flexes to keep in your pocket** for judges who push:
- `applicant_mismatch` — Rejection-Prevention blocks a doomed application because the Aadhaar
  name disagrees with the PAN record, and shows the exact fix.
- `applicant_student` — the student/mover case: Aadhaar jurisdiction is Lucknow, GPS says
  Bengaluru. The disagreement is **surfaced for an explicit choice**, never silently resolved
  (AGENTS.md §5.3).

---

## Demo personas (Module 3 mock e-KYC store)

| Applicant ID | Profile | Behaviour |
|---|---|---|
| `applicant_001` | Rohan Verma, Bengaluru | Clean — clear to submit |
| `applicant_student` | Priya Sharma, Lucknow Aadhaar / Bengaluru GPS | RTO jurisdiction disagreement → surfaced for choice |
| `applicant_mismatch` | Vikram Singh Chauhan | Aadhaar vs PAN name mismatch → submission blocked with fix |
| anything else | Generated profile | Clean — clear to submit |

The **RTO simulator** panel in the web app drives the mock government side (document
verification, test results) through Module 5, then asks Module 2 to sync.

---

## Environment flags

| Variable | Module | Default | Meaning |
|---|---|---|---|
| `JOURNEY_FAST_FORWARD` | journey | off | Collapse the 30-day practice / 7-day retest gates (demo only) |
| `IDENTITY_MODE` | journey | `http` | `http` calls the real Module 3; `stub` uses the built-in offline stub |
| `IDENTITY_URL` | journey | `http://localhost:8003` | Module 3 base URL |
| `GATEWAY_URL` | journey | `http://localhost:8005` | Module 5 base URL |
| `IDENTITY_SERVICE_URL` / `ACADEMY_SERVICE_URL` | bol-ke-apply | `http://127.0.0.1:8003` / `:8004` | Upstream services for MCP tools |
| `ACADEMY_LLM_PROVIDER` | academy | `mock` | `gemini` to use Gemini classification (needs `GEMINI_API_KEY`) |
| `VITE_JOURNEY_URL` / `VITE_GATEWAY_URL` | web | `http://localhost:8002` / `:8005` | Module 2 / Module 5 endpoints (both send CORS headers) |
| `VITE_ACADEMY_URL` | web | `/api/academy` (dev proxy) | Module 4 has no CORS headers, so the browser goes through Vite's proxy. To bypass it, set the full route base, e.g. `http://localhost:8004/academy`. |

---

## Working Agreements (from AGENTS.md)

1. **Contracts are additive-only** — do not rename or delete existing fields in
   `packages/contracts`; add fields instead, and flag changes to the other module owners.
2. **Module boundaries** — do not touch another module's directory under `services/`.
3. **External dependencies are mocked** — DigiLocker, UIDAI, and Sarathi are mocked locally so
   development never blocks on external access.
4. **GPS vs Aadhaar address** — GPS suggests the nearest RTO for convenience; the
   Aadhaar-registered address determines legal RTO jurisdiction. Never silently conflated;
   when they disagree the citizen chooses.
5. **Only Module 5 talks to government systems** — Sarathi / Vahan / eChallan traffic goes
   through the Integration Gateway and nowhere else.

## Integration decisions made during the merge

- `JourneyStage` lives once, in `contracts/enums.py`; `contracts/journey.py` re-exports it.
- Module 2 distinguishes **blocking** mismatches from **advisory** ones: a mismatch on
  `aadhaar_registered_address` routes to the RTO-confirmation flow (§5.3) instead of hard-
  blocking the application, while identity mismatches (name/DOB) still block.
- Module 2's identity client defaults to `IDENTITY_MODE=http` now that Module 3 exists; the
  offline stub mirrors the same three personas so tests never need the network.
- Module 6's journey-state tools are unblocked and declared in `contracts/mcp_tools.py`.
- Modules 2 and 5 were renamed from a shared `app` package to `journey_service` /
  `gateway_service` under `src/` — both had claimed the same top-level module name, which
  collided in the shared workspace virtualenv.
- Modules 3 and 4 send no CORS headers (they're internal services), so Module 1 reaches
  Module 4 through a Vite dev proxy rather than editing another owner's module (§11.2).
  If Module 3/4 later add CORS middleware, the proxy can simply be dropped.

## Demo-reliability features (added 28 Aug 2026)

- **Journeys survive restarts.** Modules 2 and 5 persist state to SQLite
  (`services/*/data/*.sqlite3`, gitignored). Override paths with `JOURNEY_DB` /
  `GATEWAY_DB`; tests use `:memory:`.
- **Personas are reusable.** `POST /journey/{id}/reset` (and the "Reset demo" button in the
  web header) forgets one journey so a shared demo persona can be walked again — without it,
  one visitor completing a journey consumed the persona for everyone.
- **The voice widget is real.** The web app's 🎙️ बोल के अप्लाई panel sends free text (or
  speech, where the browser supports it, with a graceful message when it doesn't) to Module
  6's `/chat`; replies show which MCP tool ran. Nothing is canned in the frontend.
- **The licence card prints.** "Print / save licence as PDF" uses a print stylesheet that
  isolates the card — a real export, not an alert claiming one.
- Mismatch severity is honored end to end: Module 3 grades mismatches
  (`severity: "error" | "warning"`), Module 2 blocks only on errors and routes warnings to
  the RTO-choice flow (§5.3).

## Known gaps / next steps

- **`VerifiedProfile` has no jurisdiction RTO code**: Module 3 computes `jurisdiction_rto`
  internally but doesn't expose it, so Module 2 derives a state code from the Aadhaar address
  (`resolve_rto_code`). Adding an additive `aadhaar_jurisdiction_rto` field to
  `VerifiedProfile` would remove that derivation.
- **LL quiz** is 3 fixed questions in the frontend; a real item bank belongs in a service.
- **Speech synthesis** (`audio_url`) is a mock-provider stub; wire a real TTS provider via
  `BOL_KE_APPLY_LLM_PROVIDER` when keys/budget are decided (AGENTS.md §10.4).
