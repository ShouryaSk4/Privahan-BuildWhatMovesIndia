# Parivahan MVP

Citizen-experience and orchestration layer over Sarathi / Vahan — see [AGENTS.md](AGENTS.md)
for module boundaries and contracts. This repo currently contains **Modules 1, 2, and 5**
(built 27 Aug 2026); Modules 3, 4, and 6 are being built in separate silos and merge here.

## Layout

```
apps/web               Module 1 — Citizen Experience (React + TS + Vite)
services/journey       Module 2 — Journey & Requirements Engine (FastAPI)
services/gateway       Module 5 — Integration Gateway, mock Sarathi (FastAPI)
packages/contracts     Shared Pydantic models — single source of truth (§7)
tools/                 OpenAPI → TypeScript type generation (§8.5)
```

## Run it

Prereqs: Python 3.11+, [uv](https://docs.astral.sh/uv/), Node 20+, pnpm.

```bash
# Terminal 1 — Module 5 (mock government side), port 8005
cd services/gateway && uv sync && uv run uvicorn app.main:app --port 8005

# Terminal 2 — Module 2, port 8002 (fast-forward collapses the 30-day/7-day waits for demos)
cd services/journey && uv sync && JOURNEY_FAST_FORWARD=1 uv run uvicorn app.main:app --port 8002

# Terminal 3 — Module 1, port 5173
pnpm install && pnpm --dir apps/web dev
```

Ports: journey **8002** · identity (Module 3, silo) **8003** · academy (Module 4, silo) **8004** · gateway **8005**.

## Tests & lint

```bash
cd services/gateway && uv run pytest && uv run ruff check .
cd services/journey && uv run pytest && uv run ruff check .
pnpm --dir apps/web test && pnpm --dir apps/web exec tsc -b
```

## Type generation (AGENTS.md §4.3 / §8.5)

Pydantic → FastAPI → OpenAPI → `openapi-typescript` → `apps/web/src/api/types/*`.
No hand-written TypeScript duplicates of shared contracts.

```bash
bash tools/gen-types.sh
```

Re-run after any contract or endpoint change, and after merging Modules 3/4/6.

## The 3-minute demo script

Run all three services with `JOURNEY_FAST_FORWARD=1` (see *Run it*), open the web app, then:

1. **The promise** *(15s)* — landing page. Point at the savings strip: the agent charges
   ₹3,500–5,000 with no receipt; this journey is ₹1,350, promised upfront with cost,
   days, and visit count. "We sell what the tout sells: certainty."
2. **Zero forms** *(40s)* — continue as `APL-0001` → "Fetch my details & start". The review
   screen says *Fields you typed: 0*. Tick, submit — an application number exists.
   Optional flex: restart as `APL-0002` to show the two-RTO disagreement being surfaced
   for an explicit choice, or `APL-0009` to show Rejection-Prevention blocking a doomed
   application with the exact fix.
3. **The test comes home** *(40s)* — open the RTO simulator (dev panel), click "RTO verifies
   documents". The learner's test appears **in the app**: answer the 3 road-rules questions,
   pass, and the learner's licence is issued — no RTO visit.
4. **The coach** *(45s)* — start the practice window, book a slot, then in the simulator fail
   the driving test at *reverse parking*. The rail shows "Retry", the missed checkpoint is
   named, and the Driving Academy opens pre-loaded with the right lesson. "Failure becomes
   a plan, not a fine."
5. **The ending** *(20s)* — rebook, pass. Confetti, and the driving licence rendered as a
   card built from the same verified data: *zero forms, one visit, a coach the whole way.*

## Demo conventions (stub identity, until Module 3 merges)

- Applicant ID ending in **2** → GPS RTO and Aadhaar-address jurisdiction disagree; the UI
  surfaces the disagreement and requires an explicit choice (§5.3 — never silently resolved).
- Applicant ID ending in **9** → name mismatch; submission is blocked with a suggested fix
  (Rejection-Prevention).
- Any other ID → clean profile, clear to submit.
- The **RTO simulator** panel in the web app drives the mock government side
  (document verification, test results) through Module 5, then syncs Module 2.

## Environment flags

| Variable | Module | Default | Meaning |
|---|---|---|---|
| `JOURNEY_FAST_FORWARD` | journey | off | Collapse the 30-day practice / 7-day retest gates (demo only) |
| `IDENTITY_MODE` | journey | `stub` | `http` to call a real Module 3 at `IDENTITY_URL` |
| `IDENTITY_URL` | journey | `http://localhost:8003` | Module 3 base URL |
| `GATEWAY_URL` | journey | `http://localhost:8005` | Module 5 base URL |
| `VITE_JOURNEY_URL` / `VITE_GATEWAY_URL` / `VITE_ACADEMY_URL` | web | localhost defaults | Service endpoints |

## Decisions on AGENTS.md §10 open questions (this round)

- **TypeScript** for the React app (Q3): yes — types are generated from OpenAPI.
- **pnpm** (Q4): yes, with a workspace at the repo root.
- **uv** (Q5): yes, with `parivahan-contracts` as an editable path dependency.
- Module 2 rules are data-driven JSON (`services/journey/app/rules/delhi.json`); a second
  state is a second file, not a rewrite (§3.3).
- Q1/Q2 (renewal scope): unchanged — out of scope, per §3.4.
- Q6–Q10 belong to Modules 3/4/6 (silo owners).
