# Module 2 — Journey & Requirements Engine (`services/journey`)

Owner: **Collaborator**  
Status: **Deferred / Next Round**

## Responsibilities (per AGENTS.md Section 5.2)
The backend brain of the platform:
- Own the journey state machine for first-time car driving licence.
- Determine required documents and steps based on verified identity from Module 3.
- Compute the Certainty Contract: exact cost in INR, timeline in days, and visit count.
- Interface with external government databases via Module 5 (Integration Gateway).

## Target Journey States (Section 6)
- `no_licence`
- `ll_application_submitted`
- `ll_documents_verified`
- `ll_test_scheduled`
- `ll_issued`
- `practice_window`
- `dl_test_booked`
- `dl_test_result_fail`
- `dl_test_result_pass`
- `dl_issued`

## Target Output Contract (Section 7.4)
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

## Working Agreements
- Keep state machine rules data-driven so future state rules can be introduced without engine rewrites.
- Depend on `/packages/contracts` for shared models.
