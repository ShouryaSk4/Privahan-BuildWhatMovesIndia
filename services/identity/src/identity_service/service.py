"""Identity Service core business logic (Module 3).

Implements Zero-Form Licence engine, DigiLocker / Aadhaar e-KYC pull,
rejection prevention mismatch checks, and strict separation of GPS nearest RTO vs
Aadhaar jurisdiction RTO.
"""

import json
import logging
from datetime import UTC, date, datetime
from pathlib import Path

from contracts.enums import IdentitySource
from contracts.identity import Mismatch, MismatchCheckResult, VerifiedProfile

logger = logging.getLogger("identity_service")

DATA_FILE = Path(__file__).parent / "data" / "citizens.json"


def _calculate_age(born: date) -> int:
    today = datetime.now(UTC).date()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


class IdentityService:
    """Service handling identity fetching and rejection prevention."""

    def __init__(self, data_path: Path | None = None):
        self._data_path = data_path or DATA_FILE
        self._records: dict[str, dict] = self._load_fixtures()

    def _load_fixtures(self) -> dict[str, dict]:
        if self._data_path.exists():
            try:
                with open(self._data_path, encoding="utf-8") as f:
                    raw_data = json.load(f)
                    parsed: dict[str, dict] = {}
                    for key, val in raw_data.items():
                        parsed[key] = {
                            **val,
                            "dob": date.fromisoformat(val["dob"]),
                        }
                        if "pan_record" in val and "dob" in val["pan_record"]:
                            parsed[key]["pan_record"]["dob"] = date.fromisoformat(
                                val["pan_record"]["dob"]
                            )
                    # Support legacy test aliases
                    parsed["applicant_001"] = parsed["applicant_clean"]
                    parsed["applicant_student"] = parsed["applicant_student_mover"]
                    parsed["applicant_mismatch"] = parsed["applicant_pan_name_mismatch"]
                    return parsed
            except (json.JSONDecodeError, OSError, KeyError, ValueError) as exc:
                logger.warning("Failed to parse fixture file %s: %s", self._data_path, exc)

        return {}

    def get_record(self, applicant_id: str) -> dict | None:
        return self._records.get(applicant_id)

    def list_personas(self) -> list[str]:
        return [k for k in self._records if not k.startswith("applicant_00")]

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
            now_utc = datetime.now(UTC)
            mock_dob = date(2002, 1, 1)
            age = _calculate_age(mock_dob)
            return VerifiedProfile(
                applicant_id=applicant_id,
                source=IdentitySource.DIGILOCKER_AADHAAR,
                name=f"Applicant {applicant_id.replace('_', ' ').title()}",
                dob=mock_dob,
                address="100 Feet Road, Koramangala, Bengaluru, KA - 560034",
                aadhaar_registered_address="100 Feet Road, Koramangala, Bengaluru, KA - 560034",
                gps_suggested_rto=gps_suggested_rto or "KA-01 Koramangala",
                addresses_match=True,
                photo_url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=300",
                fetched_at=now_utc,
                age=age,
                age_eligible=age >= 18,
            )

        dob: date = record["dob"]
        age = _calculate_age(dob)
        aadhaar_addr = record.get("aadhaar_registered_address", record["address"])
        suggested_rto = gps_suggested_rto or record.get("default_gps_rto", "KA-03 Indiranagar")
        jurisdiction_rto = record.get("jurisdiction_rto", "KA-03 Indiranagar")

        # Compare State prefix (e.g. KA, UP, DL, TN)
        suggested_state = suggested_rto.split("-")[0].strip().upper()
        jurisdiction_state = jurisdiction_rto.split("-")[0].strip().upper()
        addresses_match = suggested_state == jurisdiction_state

        return VerifiedProfile(
            applicant_id=applicant_id,
            source=record["source"],
            name=record["name"],
            dob=dob,
            address=record["address"],
            photo_url=record["photo_url"],
            gps_suggested_rto=suggested_rto,
            aadhaar_registered_address=aadhaar_addr,
            addresses_match=addresses_match,
            fetched_at=datetime.now(UTC),
            age=age,
            age_eligible=age >= 18,
        )

    def check_mismatch(self, applicant_id: str) -> MismatchCheckResult:
        """Performs Rejection-Prevention checks against secondary sources and rules."""
        profile = self.fetch_identity(applicant_id)
        record = self._records.get(applicant_id)
        mismatches: list[Mismatch] = []

        # 1. Age Eligibility Check (LMV licence requires minimum age 18)
        if profile.age is not None and profile.age < 18:
            mismatches.append(
                Mismatch(
                    field="dob",
                    fetched_value=profile.dob.isoformat(),
                    issue=f"Applicant age is {profile.age}. Motor Vehicles Act requires age 18 or above for a Light Motor Vehicle (LMV) driving licence.",
                    suggested_fix="You are eligible to apply once you reach 18 years of age. (Or apply for non-geared 50cc two-wheeler at age 16 with parental consent).",
                    severity="error",
                )
            )

        # 2. PAN Cross-Verification
        if record and "pan_record" in record:
            pan = record["pan_record"]
            # Check name consistency
            if pan.get("name") and pan["name"].strip().lower() != record["name"].strip().lower():
                mismatches.append(
                    Mismatch(
                        field="name",
                        fetched_value=record["name"],
                        issue=f"Aadhaar name '{record['name']}' differs from PAN record '{pan['name']}'.",
                        suggested_fix="Ensure full name matches across government identity databases or upload a gazette notification / marriage certificate.",
                        severity="error",
                    )
                )

            # Check DOB consistency
            if pan.get("dob") and pan["dob"] != record["dob"]:
                mismatches.append(
                    Mismatch(
                        field="dob",
                        fetched_value=record["dob"].isoformat(),
                        issue=f"Aadhaar DOB '{record['dob']}' differs from PAN DOB '{pan['dob']}'.",
                        suggested_fix="Update PAN record with income tax portal or attach Class 10 marksheet as definitive birth certificate proof.",
                        severity="error",
                    )
                )

        # 3. GPS vs Aadhaar Jurisdiction Mismatch (Student / Mover scenario)
        if profile.addresses_match is False:
            mismatches.append(
                Mismatch(
                    field="aadhaar_registered_address",
                    fetched_value=str(profile.aadhaar_registered_address),
                    issue=f"Your current device location suggests {profile.gps_suggested_rto}, but your Aadhaar jurisdiction is in another state ({profile.aadhaar_registered_address}).",
                    suggested_fix="You can apply at your legal Aadhaar jurisdiction RTO, or update your Aadhaar address with local residence proof (e.g. rental agreement or hostel certificate).",
                    severity="warning",
                )
            )

        # clear_to_submit is False if any blocking 'error' exists
        has_blocking_errors = any(m.severity == "error" for m in mismatches)
        clear_to_submit = not has_blocking_errors

        return MismatchCheckResult(
            applicant_id=applicant_id,
            mismatches=mismatches,
            clear_to_submit=clear_to_submit,
        )
