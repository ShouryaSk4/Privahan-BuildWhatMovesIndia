"""Identity Service core business logic (Module 3).

Implements Zero-Form Licence engine, DigiLocker / Aadhaar e-KYC pull,
rejection prevention mismatch checks, and strict separation of GPS nearest RTO vs
Aadhaar jurisdiction RTO.
"""

from datetime import UTC, date, datetime

from contracts.enums import IdentitySource
from contracts.identity import Mismatch, MismatchCheckResult, VerifiedProfile

# Mock database simulating DigiLocker / UIDAI e-KYC records and PAN cross-reference
MOCK_IDENTITY_STORE: dict[str, dict] = {
    "applicant_001": {
        "name": "Rohan Verma",
        "dob": date(2003, 8, 15),
        "source": IdentitySource.DIGILOCKER_AADHAAR,
        "address": "Flat 204, Palm Grove, Whitefield, Bengaluru, KA - 560066",
        "aadhaar_registered_address": "Flat 204, Palm Grove, Whitefield, Bengaluru, KA - 560066",
        "jurisdiction_rto": "KA-53 KR Puram",
        "photo_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300",
        "pan_record": {
            "name": "Rohan Verma",
            "dob": date(2003, 8, 15),
            "status": "active",
        },
    },
    # Student / Mover case: Aadhaar is Lucknow, but current GPS location is Bengaluru
    "applicant_student": {
        "name": "Priya Sharma",
        "dob": date(2004, 2, 10),
        "source": IdentitySource.DIGILOCKER_AADHAAR,
        "address": "Room 102, Kaveri Hostel, Electronic City, Bengaluru, KA - 560100",
        "aadhaar_registered_address": "House 12, Gomti Nagar, Lucknow, UP - 226010",
        "jurisdiction_rto": "UP-32 Lucknow",
        "photo_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=300",
        "pan_record": {
            "name": "Priya Sharma",
            "dob": date(2004, 2, 10),
            "status": "active",
        },
    },
    # Rejection mismatch case: PAN name spelling differs from Aadhaar
    "applicant_mismatch": {
        "name": "Vikram Singh Chauhan",
        "dob": date(2001, 11, 20),
        "source": IdentitySource.DIGILOCKER_AADHAAR,
        "address": "Sector 15, Rohini, Delhi, DL - 110089",
        "aadhaar_registered_address": "Sector 15, Rohini, Delhi, DL - 110089",
        "jurisdiction_rto": "DL-08 Rohini",
        "photo_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300",
        "pan_record": {
            "name": "Vikram S Chauhan",
            "dob": date(2001, 11, 20),
            "status": "active",
        },
    },
}


class IdentityService:
    """Service handling identity fetching and rejection prevention."""

    def __init__(self, records: dict[str, dict] | None = None):
        self._records = records if records is not None else MOCK_IDENTITY_STORE

    def fetch_identity(
        self,
        applicant_id: str,
        gps_suggested_rto: str | None = None,
    ) -> VerifiedProfile:
        """Pulls verified identity record for applicant_id.

        Separates GPS location (nearest RTO convenience) from Aadhaar registered address
        (legal jurisdiction).
        """
        record = self._records.get(applicant_id)
        if not record:
            # Generate a realistic mock profile for arbitrary applicant IDs
            return VerifiedProfile(
                applicant_id=applicant_id,
                source=IdentitySource.DIGILOCKER_AADHAAR,
                name=f"Applicant {applicant_id.replace('_', ' ').title()}",
                dob=date(2002, 1, 1),
                address="100 Feet Road, Koramangala, Bengaluru, KA - 560034",
                aadhaar_registered_address="100 Feet Road, Koramangala, Bengaluru, KA - 560034",
                gps_suggested_rto=gps_suggested_rto or "KA-01 Koramangala",
                addresses_match=True,
                photo_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=300",
                fetched_at=datetime.now(UTC),
            )

        aadhaar_addr = record.get("aadhaar_registered_address", record["address"])
        suggested_rto = gps_suggested_rto or "KA-03 Indiranagar"
        jurisdiction_rto = record.get("jurisdiction_rto", "KA-03 Indiranagar")

        # Flag whether device/GPS location aligns with Aadhaar jurisdiction
        addresses_match = suggested_rto.split("-")[0] == jurisdiction_rto.split("-")[0]

        return VerifiedProfile(
            applicant_id=applicant_id,
            source=record["source"],
            name=record["name"],
            dob=record["dob"],
            address=record["address"],
            photo_url=record["photo_url"],
            gps_suggested_rto=suggested_rto,
            aadhaar_registered_address=aadhaar_addr,
            addresses_match=addresses_match,
            fetched_at=datetime.now(UTC),
        )

    def check_mismatch(self, applicant_id: str) -> MismatchCheckResult:
        """Performs Rejection-Prevention checks against secondary sources (e.g. PAN)."""
        record = self._records.get(applicant_id)
        mismatches: list[Mismatch] = []

        if record and "pan_record" in record:
            pan = record["pan_record"]
            # Check name consistency
            if pan["name"] != record["name"]:
                mismatches.append(
                    Mismatch(
                        field="name",
                        fetched_value=record["name"],
                        issue=f"Aadhaar name '{record['name']}' differs from PAN record '{pan['name']}'.",
                        suggested_fix="Ensure full name matches government identity databases or upload gazette notification.",
                    )
                )

            # Check DOB consistency
            if pan["dob"] != record["dob"]:
                mismatches.append(
                    Mismatch(
                        field="dob",
                        fetched_value=record["dob"].isoformat(),
                        issue=f"Aadhaar DOB '{record['dob']}' differs from PAN DOB '{pan['dob']}'.",
                        suggested_fix="Update PAN record or attach Class 10 marksheet as definitive birth certificate proof.",
                    )
                )

        # Rejection prevention rule: If addresses do not match jurisdiction state, warn citizen
        profile = self.fetch_identity(applicant_id)
        if profile.addresses_match is False:
            mismatches.append(
                Mismatch(
                    field="aadhaar_registered_address",
                    fetched_value=str(profile.aadhaar_registered_address),
                    issue=f"Your current device location suggests {profile.gps_suggested_rto}, but your Aadhaar jurisdiction is in another state/district.",
                    suggested_fix="You can apply at your Aadhaar jurisdiction RTO, or update your Aadhaar address with current local residence proof.",
                )
            )

        clear_to_submit = len(mismatches) == 0
        return MismatchCheckResult(
            applicant_id=applicant_id,
            mismatches=mismatches,
            clear_to_submit=clear_to_submit,
        )
