"""Module 2 core — the journey state machine and data-driven state rules.

This is the component that replaces today's self-declared
"I hold no licence / DL / LL" selection (AGENTS.md §5.2). Rules for one state
(Delhi) load from JSON; a second state means a second rules file, not a rewrite
(§3.3, §11.4).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from contracts.journey import (
    Certainty,
    JourneyStage,
    JourneyState,
    NextAction,
    RequiredDocument,
)

from .store import KeyValueStore

RULES_DIR = Path(__file__).parent / "rules"

# Canonical ordering used to decide whether a government-side status is
# "ahead of" the locally known stage during sync.
STAGE_ORDER = [
    JourneyStage.NO_LICENCE,
    JourneyStage.LL_APPLICATION_SUBMITTED,
    JourneyStage.LL_DOCUMENTS_VERIFIED,
    JourneyStage.LL_TEST_SCHEDULED,
    JourneyStage.LL_ISSUED,
    JourneyStage.PRACTICE_WINDOW,
    JourneyStage.DL_TEST_BOOKED,
    JourneyStage.DL_TEST_RESULT_FAIL,
    JourneyStage.DL_TEST_RESULT_PASS,
    JourneyStage.DL_ISSUED,
]

# event -> (allowed source stages, destination stage)
TRANSITIONS: dict[str, tuple[tuple[JourneyStage, ...], JourneyStage]] = {
    "ll_application_submitted": (
        (JourneyStage.NO_LICENCE,),
        JourneyStage.LL_APPLICATION_SUBMITTED,
    ),
    "documents_verified": (
        (JourneyStage.LL_APPLICATION_SUBMITTED,),
        JourneyStage.LL_DOCUMENTS_VERIFIED,
    ),
    "ll_test_scheduled": (
        (JourneyStage.LL_DOCUMENTS_VERIFIED,),
        JourneyStage.LL_TEST_SCHEDULED,
    ),
    # Delhi's Aadhaar path allows the online test straight after verification,
    # so both verified and scheduled are legal sources.
    "ll_test_passed": (
        (JourneyStage.LL_DOCUMENTS_VERIFIED, JourneyStage.LL_TEST_SCHEDULED),
        JourneyStage.LL_ISSUED,
    ),
    "begin_practice": (
        (JourneyStage.LL_ISSUED, JourneyStage.DL_TEST_BOOKED),
        JourneyStage.PRACTICE_WINDOW,
    ),
    "dl_test_booked": (
        (JourneyStage.LL_ISSUED, JourneyStage.PRACTICE_WINDOW, JourneyStage.DL_TEST_BOOKED),
        JourneyStage.DL_TEST_BOOKED,
    ),
    "dl_test_failed": ((JourneyStage.DL_TEST_BOOKED,), JourneyStage.DL_TEST_RESULT_FAIL),
    "dl_test_passed": ((JourneyStage.DL_TEST_BOOKED,), JourneyStage.DL_TEST_RESULT_PASS),
    "dl_test_rebooked": (
        (JourneyStage.DL_TEST_RESULT_FAIL, JourneyStage.DL_TEST_BOOKED),
        JourneyStage.DL_TEST_BOOKED,
    ),
    "dl_issued": ((JourneyStage.DL_TEST_RESULT_PASS,), JourneyStage.DL_ISSUED),
}

# gateway-normalized government stage -> journey stage (used by sync)
GOV_STAGE_MAP: dict[str, JourneyStage] = {
    "received": JourneyStage.LL_APPLICATION_SUBMITTED,
    "documents_verified": JourneyStage.LL_DOCUMENTS_VERIFIED,
    "ll_test_passed": JourneyStage.LL_ISSUED,
    "ll_issued": JourneyStage.LL_ISSUED,
    "dl_test_booked": JourneyStage.DL_TEST_BOOKED,
    "dl_test_failed": JourneyStage.DL_TEST_RESULT_FAIL,
    "dl_test_passed": JourneyStage.DL_TEST_RESULT_PASS,
    "dl_issued": JourneyStage.DL_ISSUED,
}


class TransitionError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class GateError(Exception):
    """A transition that is legal in shape but not yet permitted by a rule gate."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass
class ApplicantRecord:
    applicant_id: str
    stage: JourneyStage = JourneyStage.NO_LICENCE
    application_number: str | None = None
    ll_issued_at: datetime | None = None
    dl_failed_at: datetime | None = None
    failed_checkpoint: str | None = None
    history: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "applicant_id": self.applicant_id,
            "stage": self.stage.value,
            "application_number": self.application_number,
            "ll_issued_at": self.ll_issued_at.isoformat() if self.ll_issued_at else None,
            "dl_failed_at": self.dl_failed_at.isoformat() if self.dl_failed_at else None,
            "failed_checkpoint": self.failed_checkpoint,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> ApplicantRecord:
        return cls(
            applicant_id=raw["applicant_id"],
            stage=JourneyStage(raw["stage"]),
            application_number=raw.get("application_number"),
            ll_issued_at=(
                datetime.fromisoformat(raw["ll_issued_at"]) if raw.get("ll_issued_at") else None
            ),
            dl_failed_at=(
                datetime.fromisoformat(raw["dl_failed_at"]) if raw.get("dl_failed_at") else None
            ),
            failed_checkpoint=raw.get("failed_checkpoint"),
            history=list(raw.get("history", [])),
        )


class Rules:
    """One state's rules, loaded from JSON. Data-driven by design (§3.3)."""

    def __init__(self, state_code: str = "delhi") -> None:
        raw = json.loads((RULES_DIR / f"{state_code}.json").read_text(encoding="utf-8"))
        self.raw = raw
        self.certainty = Certainty(**raw["certainty"])
        self.practice_window_days: int = raw["practice_window_days"]
        self.ll_validity_days: int = raw.get("ll_validity_days", 180)
        self.retest_wait_days: int = raw["retest_wait_days"]
        self.required_documents = [RequiredDocument(**d) for d in raw["required_documents"]]
        self.stages: dict[str, dict] = raw["stages"]

    def next_action(self, stage: JourneyStage) -> NextAction:
        return NextAction(**self.stages[stage.value]["next_action"])

    def detail(self, stage: JourneyStage) -> str | None:
        return self.stages[stage.value].get("detail")


def _fast_forward() -> bool:
    """Dev/demo override that collapses waiting-period gates to zero days."""
    return os.environ.get("JOURNEY_FAST_FORWARD", "").strip() in ("1", "true", "yes")


class JourneyEngine:
    def __init__(self, rules: Rules | None = None) -> None:
        self.rules = rules or Rules()
        self.store = KeyValueStore()
        # Journeys survive restarts: hydrate from the store on boot.
        self._records: dict[str, ApplicantRecord] = {
            key: ApplicantRecord.from_dict(raw) for key, raw in self.store.all().items()
        }

    # -- records -----------------------------------------------------------

    def record(self, applicant_id: str) -> ApplicantRecord:
        if applicant_id not in self._records:
            self._records[applicant_id] = ApplicantRecord(applicant_id=applicant_id)
        return self._records[applicant_id]

    def save(self, record: ApplicantRecord) -> None:
        self.store.put(record.applicant_id, record.to_dict())

    def set_application_number(self, applicant_id: str, application_number: str) -> None:
        record = self.record(applicant_id)
        record.application_number = application_number
        self.save(record)

    def reset_applicant(self, applicant_id: str) -> None:
        """Demo reset: forget one journey so a persona can be walked again."""
        self._records.pop(applicant_id, None)
        self.store.delete(applicant_id)

    def reset(self) -> None:
        for applicant_id in list(self._records):
            self.reset_applicant(applicant_id)

    # -- gates ---------------------------------------------------------------

    def check_gate(self, record: ApplicantRecord, event: str) -> None:
        now = datetime.now(UTC)
        if event == "dl_test_booked" and not _fast_forward():
            if record.ll_issued_at is None:
                raise GateError("Cannot book a driving test before the learner's licence exists.")
            eligible_at = record.ll_issued_at + timedelta(days=self.rules.practice_window_days)
            if now < eligible_at:
                days_left = (eligible_at - now).days + 1
                raise GateError(
                    f"The {self.rules.practice_window_days}-day practice window is still open — "
                    f"booking unlocks in about {days_left} day(s)."
                )
        if (
            event == "dl_test_rebooked"
            and not _fast_forward()
            and record.dl_failed_at is not None
        ):
            eligible_at = record.dl_failed_at + timedelta(days=self.rules.retest_wait_days)
            if now < eligible_at:
                days_left = (eligible_at - now).days + 1
                raise GateError(
                    f"A retest can be booked {self.rules.retest_wait_days} days after the "
                    f"failed attempt — about {days_left} day(s) to go."
                )

    # -- transitions ---------------------------------------------------------

    def apply_event(self, applicant_id: str, event: str) -> ApplicantRecord:
        record = self.record(applicant_id)
        if event not in TRANSITIONS:
            raise TransitionError(f"Unknown event '{event}'.")
        sources, destination = TRANSITIONS[event]
        if record.stage not in sources:
            raise TransitionError(
                f"Event '{event}' is not valid from stage '{record.stage.value}'."
            )
        self.check_gate(record, event)

        now = datetime.now(UTC)
        if destination == JourneyStage.LL_ISSUED:
            record.ll_issued_at = now
        if destination == JourneyStage.DL_TEST_RESULT_FAIL:
            record.dl_failed_at = now
        record.stage = destination
        record.history.append(event)
        self.save(record)
        return record

    def sync_from_gov(
        self, applicant_id: str, gov_stage: str, failed_checkpoint: str | None = None
    ) -> ApplicantRecord:
        """Fold a government-side status (via Module 5) into the journey.

        Only ever moves forward; practice_window is a local stage the
        government side doesn't know about, so it is never regressed.
        """
        record = self.record(applicant_id)
        mapped = GOV_STAGE_MAP.get(gov_stage)
        if mapped is None:
            return record
        if STAGE_ORDER.index(mapped) > STAGE_ORDER.index(record.stage):
            if mapped == JourneyStage.LL_ISSUED and record.ll_issued_at is None:
                record.ll_issued_at = datetime.now(UTC)
            if mapped == JourneyStage.DL_TEST_RESULT_FAIL:
                record.dl_failed_at = datetime.now(UTC)
                record.failed_checkpoint = failed_checkpoint
            record.stage = mapped
            record.history.append(f"sync:{gov_stage}")
            self.save(record)
        return record

    # -- projection ----------------------------------------------------------

    def state(self, applicant_id: str) -> JourneyState:
        record = self.record(applicant_id)
        detail = self.rules.detail(record.stage)
        if record.stage == JourneyStage.PRACTICE_WINDOW and record.ll_issued_at is not None:
            day = (datetime.now(UTC) - record.ll_issued_at).days + 1
            detail = (
                f"Day {min(day, self.rules.practice_window_days)} of "
                f"{self.rules.practice_window_days} in your practice window. {detail}"
            )
        if record.stage == JourneyStage.DL_TEST_RESULT_FAIL and record.failed_checkpoint:
            detail = f"Missed checkpoint: {record.failed_checkpoint}. {detail}"
        # LL expiry: live from issuance until the DL is in hand.
        ll_valid_till = None
        if record.ll_issued_at is not None and record.stage != JourneyStage.DL_ISSUED:
            ll_valid_till = (
                record.ll_issued_at + timedelta(days=self.rules.ll_validity_days)
            ).date().isoformat()
        return JourneyState(
            applicant_id=applicant_id,
            journey_type="first_time_licence",
            current_stage=record.stage,
            next_action=self.rules.next_action(record.stage),
            certainty=self.rules.certainty,
            required_documents=(
                self.rules.required_documents
                if record.stage == JourneyStage.NO_LICENCE
                else []
            ),
            stage_detail=detail,
            application_number=record.application_number,
            ll_valid_till=ll_valid_till,
        )


_engine: JourneyEngine | None = None


def get_engine() -> JourneyEngine:
    global _engine
    if _engine is None:
        _engine = JourneyEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None
