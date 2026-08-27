# Module 6 — Bol Ke Apply

Owner: **You**  
Status: **Active — Ready to Build**

## Overview
A voice/conversational front door for citizens who prefer not to use traditional web forms. Bol Ke Apply is not a new engine; it is a second way to interact with the same underlying platform services.

It is implemented as an **MCP (Model Context Protocol) Server** exposing core platform capabilities as MCP tools, intended to be driven by a conversational LLM (Gemini or OpenAI).

## Exposed Tools (AGENTS.md Section 7.3)
- `fetch_identity(applicant_id: str)`: Wraps Module 3 identity pull.
- `check_mismatch(applicant_id: str)`: Wraps Module 3 rejection prevention.
- `match_video(applicant_id: str, query: str, journey_stage: str | None)`: Wraps Module 4 video matching.

> **Note on Journey-State Tools:** Tools like `start_application`, `whats_next`, and `book_test` depend on Module 2 (Journey Engine) and will be integrated once Module 2 is built by your collaborator.

## Running Independently
From repository root:
```powershell
uv run --package bol-ke-apply python -m bol_ke_apply.server
```

## Testing
```powershell
uv run pytest services/bol-ke-apply
```
