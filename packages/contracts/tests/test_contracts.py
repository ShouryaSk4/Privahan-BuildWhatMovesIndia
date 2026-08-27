"""Unit tests for shared contracts package."""

from datetime import UTC, date, datetime

from contracts import (
    IdentitySource,
    JourneyStage,
    Mismatch,
    MismatchCheckResult,
    VerifiedProfile,
    VideoMatchRequest,
    VideoMatchResult,
)


def test_verified_profile_instantiation():
    profile = VerifiedProfile(
        applicant_id="app_123",
        source=IdentitySource.DIGILOCKER_AADHAAR,
        name="Aarav Sharma",
        dob=date(2002, 5, 14),
        address="Flat 402, Green Meadows, Indiranagar, Bengaluru, KA - 560038",
        photo_url="https://storage.parivahan.internal/photos/app_123.jpg",
        gps_suggested_rto="KA-03 Indiranagar",
        aadhaar_registered_address="Flat 402, Green Meadows, Indiranagar, Bengaluru, KA - 560038",
        addresses_match=True,
        fetched_at=datetime.now(UTC),
    )
    assert profile.applicant_id == "app_123"
    assert profile.addresses_match is True


def test_mismatch_check_result():
    result = MismatchCheckResult(
        applicant_id="app_456",
        mismatches=[
            Mismatch(
                field="dob",
                fetched_value="14-05-2002",
                issue="Aadhaar DOB differs from PAN DOB (15-05-2002)",
                suggested_fix="Update PAN card or upload 10th marksheet as date-of-birth proof",
            )
        ],
        clear_to_submit=False,
    )
    assert len(result.mismatches) == 1
    assert result.clear_to_submit is False


def test_academy_video_match_contracts():
    req = VideoMatchRequest(
        applicant_id="app_123",
        query="How do I do an 8 turn?",
        journey_stage=JourneyStage.PRACTICE_WINDOW,
    )
    res = VideoMatchResult(
        video_id="vid_01_eight_turn",
        topic="8-turn",
        confidence=0.95,
        fallback_message=None,
    )
    assert req.query == "How do I do an 8 turn?"
    assert res.confidence >= 0.9
