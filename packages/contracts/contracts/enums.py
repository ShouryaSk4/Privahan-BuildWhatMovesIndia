"""Shared enums defining system vocabulary from AGENTS.md Section 6."""

from enum import Enum


class JourneyStage(str, Enum):
    """Stable journey stages for the first-time car licence journey."""

    NO_LICENCE = "no_licence"
    LL_APPLICATION_SUBMITTED = "ll_application_submitted"
    LL_DOCUMENTS_VERIFIED = "ll_documents_verified"
    LL_TEST_SCHEDULED = "ll_test_scheduled"
    LL_ISSUED = "ll_issued"
    PRACTICE_WINDOW = "practice_window"
    DL_TEST_BOOKED = "dl_test_booked"
    DL_TEST_RESULT_FAIL = "dl_test_result_fail"
    DL_TEST_RESULT_PASS = "dl_test_result_pass"
    DL_ISSUED = "dl_issued"


class IdentitySource(str, Enum):
    """Source of citizen identity data."""

    DIGILOCKER_AADHAAR = "digilocker_aadhaar"
    PAN = "pan"
    MANUAL = "manual"
