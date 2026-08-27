# Module 1 — Citizen Experience (`apps/web`)

Owner: **Collaborator**  
Status: **Deferred / Next Round**

## Responsibilities
The primary frontend citizen interface:
- Single-journey first-time licence flow (No Licence → LL → 30-day Practice → DL Test → DL Issued).
- Zero-Form Review & Confirm screen (renders verified Aadhaar / DigiLocker data from Module 3).
- Status & Certainty timeline tracker (receives state from Module 2).
- Driving Academy chat widget (interacts with Module 4).

## Tech Stack (per AGENTS.md Section 4.1)
- **Framework:** React.js
- **Language:** TypeScript
- **Bundler:** Vite
- **Package Manager:** pnpm / npm
- **Testing:** Vitest + React Testing Library

## Contract Sync with Backend
Shared data contracts are defined in `/packages/contracts`.
FastAPI automatically generates an OpenAPI spec from these Pydantic models.

To generate TypeScript interfaces:
```powershell
npx openapi-typescript http://localhost:8003/openapi.json -o src/types/identity.d.ts
npx openapi-typescript http://localhost:8004/openapi.json -o src/types/academy.d.ts
```
Do not hand-write duplicate TypeScript interfaces for shared backend models.
