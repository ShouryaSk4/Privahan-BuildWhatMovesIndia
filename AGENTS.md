# AGENTS.md — Parivahan MVP

> **Shared context for every agent — human or AI — building a module of this system.**
>
> Read this file before writing code in any module. If something here conflicts with what you're about to build, **this file wins**: open a change to it rather than quietly diverging, because other modules are coding against what's written here.

**Updated:** 27 Aug 2026  
**Purpose:** Shared engineering context, module boundaries, contracts, build status, and working agreements for the Parivahan MVP.

---

## 1. What We're Building

A citizen-experience and orchestration layer that sits on top of the existing **Sarathi / Vahan / eChallan** infrastructure — not a replacement for it.

The MVP proves exactly one journey end to end:

**First-time car licence**
→ “I want to get my first licence”
→ application
→ learner's licence
→ 30-day practice window
→ driving test
→ licence in hand

The MVP is built around three ideas:

1. **Zero-Form Licence** — a form-free application using verified identity data.
2. **Driving Academy** — an AI-assisted 30-day practice window.
3. **Bol Ke Apply** — a voice/conversational front door.

The core product test is simple:

> **If this journey feels ten times simpler than today's Sarathi, the MVP has done its job.**

---

## 2. Build Status & Merge Plan

> **Status update — 27 Aug 2026:** Modules **1, 2, and 5** were built in this repo in a
> second build round (see `apps/web`, `services/journey`, `services/gateway`, and the
> README). Contract changes were additive only: `JourneyState.application_number` and
> `GovApplicationStatus.failed_checkpoint`. Since Module 2 now exists, Module 6 may add
> the journey-state tools listed in `packages/contracts/mcp_tools.py`. The silo notes
> below are retained as written for the Module 3/4/6 owners.

### Active Now

The following modules are being built in silos:

- **Module 3 — Identity & Document Service**
- **Module 4 — Driving Academy Assistant**
- **Module 6 — Bol Ke Apply**

### Deferred This Round

The following modules are **not** being built in the current round:

- **Module 1 — Citizen Experience**
- **Module 2 — Journey & Requirements Engine**
- **Module 5 — Integration Gateway**

Their sections remain in this document because Modules 3, 4, and 6 must build against their eventual interfaces.

### Merge Target

**28 Aug 2026** — tomorrow, based on the document's update date.

If that date changes, the branching and merge rules in Section 8 remain the same.

### Important Consequence for Module 6

Module 6 is intended to be:

> **“A second front door into the same engines.”**

However, Module 2 — the journey engine — does not exist in this build round.

Therefore, until Module 2 ships:

- Module 6 may expose **Module 3 identity functions**.
- Module 6 may expose **Module 4 video-matching functions**.
- Module 6 must **not** stub journey-state tools such as:
  - start application
  - what's next
  - book test

Those journey-state tools should be added when Module 2 exists.

---

## 3. Locked Scope Decisions

### 3.1 In Scope for the MVP

- One journey only:
  - no licence
  - LL application submitted
  - LL test
  - LL issued
  - 30-day practice window
  - DL test booking
  - DL test
  - DL issued
- Web only, eventually. The web shell (Module 1) is not being built this round.
- Identity through **DigiLocker / Aadhaar e-KYC**, with PAN as a secondary signal.
- Driving Academy uses a fixed library of pre-generated videos (target: approximately 10).
- Driving Academy matches the user's question to an existing video; it does not generate videos live.
- The **informational half of the Certainty Contract** — exact cost, timeline, and visit count — will come from Module 2 once it exists.
- **Bol Ke Apply** is a voice/conversational front door implemented as an MCP server exposing site functions as tools, driven by a third-party LLM.

### 3.2 Explicitly Out of Scope

Do **not** build the following into the MVP:

- WhatsApp delivery of any kind.
- Live / on-the-fly video generation.
- The Certainty Contract's one-visit **guarantee**. The operational half requires RTO floor-ops integration and is a separate project.
- Women's Licence Programme.
- Renewal.
- Duplicate licence.
- Address-change journeys.
- Any journey other than first-time licence.
- Multi-state rule variance.

### 3.3 State-Scope Rule

Model one state's rules for the MVP.

However:

- Keep Module 2 data-driven.
- A second state should not require rewriting the engine.
- Do **not** build the second state now.

### 3.4 Scope Correction

> **Fixed from the last edit:** “Renewal / duplicate / address-change” had ended up listed as both in-scope and out-of-scope.

Nothing else in this document — including Module 2's state machine and the contracts in Section 7 — supports a renewal journey.

Therefore, renewal / duplicate / address-change remain **out of scope**.

If renewal was actually intended to be in scope, treat that as a larger scope change rather than changing a single bullet.

---

## 4. Tech Stack

## 4.1 Frontend

- **Framework:** React.js
- **Language:** TypeScript (recommended)
- **Bundler:** Vite
- **Package manager:** pnpm
- **Testing:** Vitest + React Testing Library
- **Lint / format:** ESLint + Prettier

### Why TypeScript?

“Cross-reference ability should be very high” is an explicit goal.

Static types are therefore recommended because the frontend talks to three independently-built Python services.

TypeScript is the cheapest insurance against contract drift.

If the team deliberately chooses plain JavaScript, flag that decision rather than silently changing the standard.

### Why pnpm?

pnpm is recommended because of workspace support.

This becomes relevant once:

```text
/apps/web
/services/*
/packages/contracts
```

sit in the same repository.

---

## 4.2 Backend

- **Language:** Python
- **Framework:** FastAPI
- **Dependency management:** uv
- **Testing:** pytest
- **Lint / format:** Ruff

### Why FastAPI?

FastAPI generates an OpenAPI schema directly from the Pydantic models.

That schema is the concrete mechanism used to keep frontend and backend contracts aligned.

### Dependency Manager

`uv` is the default recommendation.

`poetry` is acceptable if the team already has a strong preference or existing setup.

Do not create unnecessary migration work solely to match this document.

---

## 4.3 Keeping Frontend and Backend in Sync

Every shared data shape must be defined once in:

```text
/packages/contracts
```

as a Pydantic model.

### Rules

- Do **not** hand-write duplicate TypeScript interfaces for shared backend contracts.
- FastAPI generates OpenAPI from the Pydantic models.
- Run `openapi-typescript` against the OpenAPI spec.
- Use the generated TypeScript types in the React application.

### Source of Truth

```text
Pydantic models
       ↓
    FastAPI
       ↓
   OpenAPI spec
       ↓
openapi-typescript
       ↓
TypeScript types
```

`packages/contracts` is the single source of truth for shared data shapes.

---

## 4.4 Module 6 — Bol Ke Apply

Module 6 uses:

- **Python**
- **Official MCP SDK**

The conversational layer is driven by a third-party LLM:

- Gemini, or
- GPT

The MVP should pick **one** provider rather than building against both.

If the provider is genuinely undecided, create a thin provider interface so the underlying provider can be swapped later without rewriting Module 6.

---

# 5. The Six Modules

## 5.1 Module 1 — Citizen Experience

**Status:** Deferred

The only surface a citizen directly touches.

### Responsibilities

- Application flow
- Status view
- Driving Academy chat widget
- Client-side validation
- “Review and confirm” screen for fetched identity data

### Calls

- Module 2 — what's next
- Module 3 — start eKYC / show fetched profile
- Module 4 — chat / video

### MVP Cut

- One journey only.
- No voice UI of its own; that is Module 6.
- No women's variant.
- No WhatsApp.

---

## 5.2 Module 2 — Journey & Requirements Engine

**Status:** Deferred

The backend brain of the system.

It tracks where an applicant is and determines what is required next.

This is the component that replaces today's self-declared:

> “I hold no licence / DL / LL”

style of state selection.

### Responsibilities

- Own the journey state machine.
- Determine required documents.
- Determine required steps.
- Produce cost.
- Produce timeline.
- Produce visit-count information.
- Integrate verified information from Module 3.
- Communicate with government systems through Module 5.

### Calls

- Module 3 — what is already verified
- Module 5 — submit to / read from government systems

### MVP Cut

- One state's rules.
- Rules are hardcoded initially but structured for extension.

---

## 5.3 Module 3 — Identity & Document Service

**Status:** Active — building now

This is the **Zero-Form Licence engine**.

### Responsibilities

- DigiLocker / Aadhaar e-KYC pull:
  - name
  - date of birth
  - address
  - photo
- PAN fallback / cross-check
- Rejection-Prevention mismatch check

### Important: Two Different Locations

Do **not** conflate these two concepts.

#### A. Device / GPS Location

Used only to:

> Suggest the nearest RTO for convenience.

#### B. Aadhaar-Registered Address

Used to:

> Determine RTO jurisdiction.

These can legitimately disagree for applicants such as:

- students
- recent movers

The system must **surface the disagreement**.

It must not silently choose one.

### Depends On

DigiLocker / UIDAI e-KYC access.

See Section 9 — this is not purely an engineering dependency.

---

## 5.4 Module 4 — Driving Academy Assistant

**Status:** Active — building now

The chat widget where a learner describes what they are struggling with and receives the best-matching video.

### Responsibilities

- Maintain the Driving Academy video library.
- Match user questions to the relevant video.
- Return the best matching video with confidence.

### MVP Library

Target:

**~10 pre-generated clips**

### MVP Matching Strategy

With approximately 10 videos, do **not** build an embeddings pipeline yet.

Use a single LLM classification call:

> “Which of these topics best matches this message?”

This is simpler and appropriate at this scale.

### Revisit Retrieval When

The library grows beyond a few dozen clips.

At that point, consider proper retrieval / embeddings.

### Video Generation

Live / on-the-fly generation is an eventual direction, but is **not part of this MVP**.

### Already-Named Topics

1. 8-turn
2. Reverse parking
3. Hill start
4. Clutch control
5. Steering

Five additional topics are still required to reach approximately 10.

See Section 10.

---

## 5.5 Module 5 — Integration Gateway

**Status:** Deferred

The **only module allowed to talk to Sarathi / Vahan / eChallan**.

### Responsibilities

- Own all outbound calls to government systems.
- Present a stable internal interface to the rest of the platform.

### MVP Approach

Real access is unlikely to exist yet.

Therefore:

- Build against a mock.
- Make the mock mirror expected request / response shapes.
- Keep one clean swap point for eventual real integrations.

### Hard Rule

> **No other module calls Sarathi / Vahan / eChallan directly.**

Even during rapid development.

---

## 5.6 Module 6 — Bol Ke Apply

**Status:** Active — building now

A voice/conversational front door for people who will not use a traditional web form.

It is:

> **Not a new engine.**

It is a second way to reach the same backend functions.

### Responsibilities

- Own the MCP server.
- Expose platform functions as MCP tools.
- Let a third-party conversational LLM drive the platform through those tools.

### For the Next Merge

Module 6 should wrap:

- Module 3:
  - identity fetch
  - mismatch check
- Module 4:
  - video match

### Not Yet

Do **not** build Module 2 journey-state tools until Module 2 exists.

Examples:

- what's next
- start application
- book test

### MVP Cut

- Web-adjacent widget / flow.
- Not a phone channel.
- Not WhatsApp.

The no-WhatsApp rule is about the delivery channel; it does not prohibit voice as an interaction mode.

---

# 6. Shared Vocabulary

Use these names consistently across all modules.

Do **not** create local synonyms.

| Term | Meaning |
|---|---|
| `applicant_id` | Stable identifier for a citizen across all modules |
| `journey_stage` | Enum: `no_licence`, `ll_application_submitted`, `ll_documents_verified`, `ll_test_scheduled`, `ll_issued`, `practice_window`, `dl_test_booked`, `dl_test_result_fail`, `dl_test_result_pass`, `dl_issued` |
| `verified_profile` | Output of Module 3 — fetched identity fields plus source and timestamp |
| `mismatch` | A field where fetched data will not clear the RTO's own record — Module 3's Rejection-Prevention output |
| MCP tool names | Mirror the underlying function name 1:1. Example: `fetch_identity` maps directly to `fetch_identity()` in Module 3 |

---

# 7. Cross-Module Contracts

These are **real Pydantic models**, not illustrative JSON.

Put them in:

```text
/packages/contracts
```

Modules 3, 4, and 6 must import the shared classes rather than retyping equivalent models.

## 7.1 Identity Contract

```python
# packages/contracts/identity.py

from datetime import date, datetime

from pydantic import BaseModel


class VerifiedProfile(BaseModel):
    applicant_id: str
    source: str  # "digilocker_aadhaar" | "pan" | "manual"
    name: str
    dob: date
    address: str
    photo_url: str
    gps_suggested_rto: str | None = None
    aadhaar_registered_address: str | None = None
    addresses_match: bool | None = None
    fetched_at: datetime


class Mismatch(BaseModel):
    field: str
    fetched_value: str
    issue: str
    suggested_fix: str


class MismatchCheckResult(BaseModel):
    applicant_id: str
    mismatches: list[Mismatch]
    clear_to_submit: bool
```

---

## 7.2 Driving Academy Contract

```python
# packages/contracts/academy.py

from pydantic import BaseModel


class VideoMatchRequest(BaseModel):
    applicant_id: str
    query: str
    journey_stage: str | None = None


class VideoMatchResult(BaseModel):
    video_id: str
    topic: str
    confidence: float
    fallback_message: str | None = None
```

---

## 7.3 MCP Tool Contract

```python
# packages/contracts/mcp_tools.py

# Module 6 wraps these two contracts as MCP tools for the next merge.
#
# Nothing else is exposed until Module 2 exists.

# tool "fetch_identity"(applicant_id: str) -> VerifiedProfile
# tool "check_mismatch"(applicant_id: str) -> MismatchCheckResult
# tool "match_video"(request: VideoMatchRequest) -> VideoMatchResult
```

---

## 7.4 Deferred Module 2 Contract

Module 2 does not exist yet.

Keep this contract for reference; do not stub it in Module 6.

```json
{
  "applicant_id": "string",
  "journey_type": "first_time_licence",
  "current_stage": "practice_window",
  "next_action": {
    "type": "book_dl_test",
    "label": "Book your driving test"
  },
  "certainty": {
    "cost_inr": 1350,
    "eta_days": 21,
    "visit_count": 1
  }
}
```

---

# 8. Repo Structure & Merge Plan

## 8.1 Repository Structure

```text
/parivahan-mvp
├── /apps
│   └── /web                  # React app — Module 1 shell, not built this round
│
├── /services
│   ├── /identity             # Module 3 — Python/FastAPI
│   ├── /academy               # Module 4 — Python/FastAPI
│   └── /bol-ke-apply          # Module 6 — Python, MCP server
│
├── /packages
│   └── /contracts             # Shared Pydantic models — single source of truth
│
└── AGENTS.md
```

## 8.2 Branching Rule

Each active module works from its own branch off `main`.

Current active modules:

- Module 3
- Module 4
- Module 6

### Ownership Rules

Each module branch should touch only:

```text
/services/<module>
```

plus additive changes to:

```text
/packages/contracts
```

when necessary.

---

## 8.3 Contract Change Rule

`/packages/contracts` is the **only shared surface** during silo development.

Therefore:

1. Flag contract changes to the other active module owners before merging.
2. During the silo phase, contracts are **additive-only**.
3. Add fields rather than renaming or removing fields another module may already consume.
4. Deprecate instead of breaking.

---

## 8.4 Merge Order

Merge in this order:

### Step 1 — Contracts

Fast-forward any additive contract changes into `main`.

### Step 2 — Service Modules

Merge:

- Module 3
- Module 4
- Module 6

in any order.

These modules do not depend on each other's implementation code.

They depend on:

```text
/packages/contracts
```

---

## 8.5 Post-Merge Type Generation

After the merges:

1. Generate the OpenAPI schema.
2. Run `openapi-typescript`.
3. Refresh the React application's generated types.

This is required even though Module 1 was not actively developed during the silo round.

---

## 8.6 Local Verification

Each active module must have a minimal way to run and test independently.

Examples:

- small local script
- local harness
- module-specific test command

Do **not** wait for Modules 1, 2, or 5 to exist before verifying your own module.

---

# 9. External Dependencies That Are Not Engineering Problems

Some critical dependencies are outside normal sprint execution.

Track them separately rather than treating them as code blockers.

## 9.1 DigiLocker / UIDAI e-KYC

Requires an actual:

- empanelled partner (AUA / KUA), or
- licensed aggregator in front of the service

No amount of engineering velocity removes this dependency.

Track it on the product / partnership timeline.

---

## 9.2 Sarathi / Vahan / eChallan

Government-system access is a separate dependency.

Module 5 exists so the rest of the platform can proceed without waiting for direct production access.

Use mocks while real access is unavailable.

---

## 9.3 Third-Party LLM Access

Module 6 needs:

- API key
- quota
- cost ownership
- confirmed provider

Before the merge, confirm:

1. Which provider is being used.
2. Who owns the account.
3. What quota / spending limits apply.

---

# 10. Open Questions

Resolve these before implementation moves too far.

## 10.1 Scope

1. Confirm the renewal-scope fix in Section 3.
   - Was “renewal in scope” intentional?
   - Or was it a copy-paste artifact?

2. Confirm that renewal, duplicate, and address-change remain out of scope.

---

## 10.2 Frontend

3. Confirm **TypeScript vs plain JavaScript** for the React app.

4. Confirm **pnpm vs npm**.

---

## 10.3 Backend

5. Confirm **uv vs poetry**.

---

## 10.4 Bol Ke Apply

6. Confirm **Gemini vs GPT** for Module 6.

Avoid implementing both for the MVP.

---

## 10.5 Identity & Jurisdiction

7. Confirm the Module 3 interpretation:

```text
GPS location
    ↓
nearest-RTO suggestion

Aadhaar registered address
    ↓
RTO jurisdiction
```

These must remain separate values and should be surfaced separately when they disagree.

---

## 10.6 Driving Academy

8. Confirm the other five Driving Academy topics.

Suggested placeholders:

- lane change
- parallel parking
- emergency braking
- mirror and signal checks
- gradient descent

9. Confirm the LLM-classification approach for Module 4.

10. Decide whether Module 4 should use the same LLM provider as Module 6 or an independent provider.

---

# 11. Working Agreement

These are mandatory operating rules during silo development.

## 11.1 Contracts

- Do not change Section 7 / `packages/contracts` silently.
- Flag shared contract changes to the other active module owners.
- Keep contract changes additive-only.
- Do not rename or remove fields that another module may already consume.
- Deprecate fields instead of breaking them.

## 11.2 Module Boundaries

- Do not touch another module's directory under `/services`.
- Each module owns its own implementation.
- Cross-module integration happens through shared contracts and defined interfaces.

## 11.3 External Systems

- Mock DigiLocker / UIDAI access where required.
- Mock Sarathi / Vahan / eChallan access where required.
- Do not block local development on external access controlled by third parties.

## 11.4 Module 2

Even though only one state ships in the MVP:

> Keep Module 2's rules data-driven.

Do not hardwire assumptions in other modules that make a future second state impossible.

## 11.5 General Rule

When implementation pressure conflicts with these boundaries:

> **Stop, flag the conflict, and change the shared contract or architecture deliberately. Do not quietly diverge.**
