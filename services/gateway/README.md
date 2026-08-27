# Module 5 — Integration Gateway (`services/gateway`)

Owner: **Collaborator**  
Status: **Deferred / Next Round**

## Responsibilities (per AGENTS.md Section 5.5)
The **only module allowed to talk to Sarathi / Vahan / eChallan**.

- Own all outbound calls to government systems.
- Present a stable internal interface to the rest of the platform.
- Build against high-fidelity mocks initially.
- Keep one clean swap point for eventual real API integrations.

## Hard Architectural Rule
> **No other module calls Sarathi / Vahan / eChallan directly.**  
> Even during rapid local prototyping.
