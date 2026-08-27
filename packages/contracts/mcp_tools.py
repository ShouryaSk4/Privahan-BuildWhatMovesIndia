# packages/contracts/mcp_tools.py

# Module 6 wraps these two contracts as MCP tools for the next merge.
#
# Nothing else is exposed until Module 2 exists.

# tool "fetch_identity"(applicant_id: str) -> VerifiedProfile
# tool "check_mismatch"(applicant_id: str) -> MismatchCheckResult
# tool "match_video"(request: VideoMatchRequest) -> VideoMatchResult

# --- Module 2 now exists (built 27 Aug 2026). ---
# Journey-state tools may now be added by Module 6 per AGENTS.md §2:
#
# tool "whats_next"(applicant_id: str) -> JourneyState
# tool "start_application"(applicant_id: str) -> JourneyState
# tool "report_event"(event: JourneyEvent) -> JourneyState
#
# These mirror Module 2's HTTP interface 1:1 (see services/journey).
# Module 6 owns the wrapping; this file only records the contract.
