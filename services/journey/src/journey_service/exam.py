"""Server-authoritative STALL exam (Module 2).

The correct answers live HERE, never in the browser. The client fetches
questions with the answer key stripped, submits raw answers, and the server
scores them — the citizen's browser can no longer grade itself or self-report
a pass.

Proctoring integrity is likewise recomputed server-side from the submitted
event log using the same weights the client shows, so a client that claims
"clear" while its events say otherwise is overridden.
"""

from __future__ import annotations

from pydantic import BaseModel

PASS_MARK = 3

# id, prompt, options, correct index, explanation, icon
_QUESTIONS: list[dict] = [
    {
        "id": "triangle",
        "prompt": "A red-bordered triangle sign with an exclamation mark means:",
        "options": [
            "General caution — slow down and stay alert",
            "Compulsory horn zone",
            "No parking beyond this point",
        ],
        "correct": 0,
        "explanation": "A red triangle is a cautionary sign warning of a hazard ahead.",
        "icon": "⚠️",
    },
    {
        "id": "zebra",
        "prompt": "A pedestrian is waiting at a zebra crossing. You should:",
        "options": [
            "Sound the horn and keep moving",
            "Stop and let them cross",
            "Speed up to clear the crossing first",
        ],
        "correct": 1,
        "explanation": "Pedestrians have right of way at a zebra crossing — stop and let them cross.",
        "icon": "🚸",
    },
    {
        "id": "school",
        "prompt": "Passing a school zone, the safe speed is:",
        "options": ["60 km/h", "40 km/h", "25 km/h"],
        "correct": 2,
        "explanation": "School zones require crawling speed (≈25 km/h) — children are unpredictable.",
        "icon": "🏫",
    },
    {
        "id": "roundabout",
        "prompt": "At an unmarked roundabout, you give way to:",
        "options": [
            "Traffic already on the roundabout (from your right)",
            "Traffic entering from your left",
            "Nobody — you always have priority",
        ],
        "correct": 0,
        "explanation": "At a roundabout, give way to traffic already circulating, which comes from your right.",
        "icon": "🔄",
    },
    {
        "id": "ambulance",
        "prompt": "When an emergency ambulance with sirens approaches from behind, you must:",
        "options": [
            "Accelerate quickly to stay ahead",
            "Pull safely to the left edge and give clear right of way",
            "Maintain your current lane and speed",
        ],
        "correct": 1,
        "explanation": "Rule 115 CMVR: pull to the left and give unobstructed passage to emergency vehicles.",
        "icon": "🚑",
    },
]

# Signal weights — MUST mirror apps/web/src/proctor/engine.ts so the tier the
# citizen sees and the tier the server records agree.
_WEIGHTS: dict[str, int] = {
    "tab_hidden": 12,
    "window_blur": 4,
    "fullscreen_exit": 6,
    "face_absent": 8,
    "multiple_faces": 15,
    "copy_paste": 6,
    "context_menu": 2,
    "camera_denied": 0,
    "camera_unavailable": 0,
}
_CLEAR_MIN = 85
_REVIEW_MIN = 60


class ExamQuestion(BaseModel):
    id: str
    prompt: str
    options: list[str]
    icon: str | None = None


class ExamPaper(BaseModel):
    questions: list[ExamQuestion]
    pass_mark: int
    total: int


class IntegritySubmission(BaseModel):
    camera: str = "unavailable"  # "on" | "denied" | "unavailable"
    events: list[dict] = []  # [{type, t, detail}]
    # The client's own tier/score are advisory only; the server recomputes.


class ExamSubmission(BaseModel):
    answers: list[int | None]
    integrity: IntegritySubmission | None = None


class QuestionOutcome(BaseModel):
    id: str
    correct_index: int
    was_correct: bool
    explanation: str


class ExamResult(BaseModel):
    passed: bool
    score: int
    total: int
    outcomes: list[QuestionOutcome]
    integrity_score: int
    integrity_tier: str


def paper() -> ExamPaper:
    """Public exam paper — answer key stripped."""
    return ExamPaper(
        questions=[
            ExamQuestion(id=q["id"], prompt=q["prompt"], options=q["options"], icon=q["icon"])
            for q in _QUESTIONS
        ],
        pass_mark=PASS_MARK,
        total=len(_QUESTIONS),
    )


def recompute_integrity(sub: IntegritySubmission | None) -> tuple[int, str]:
    """Server-authoritative integrity score + tier from the submitted events."""
    if sub is None:
        return 100, "review"  # no evidence at all → a human should look
    score = 100
    for ev in sub.events:
        score -= _WEIGHTS.get(str(ev.get("type", "")), 0)
    score = max(0, min(100, score))

    if score >= _CLEAR_MIN:
        tier = "clear"
    elif score >= _REVIEW_MIN:
        tier = "review"
    else:
        tier = "flagged"
    # Equity + evidence rule: no live camera → never "clear", a human reviews.
    if tier == "clear" and sub.camera != "on":
        tier = "review"
    return score, tier


def grade(sub: ExamSubmission) -> ExamResult:
    answers = list(sub.answers) + [None] * (len(_QUESTIONS) - len(sub.answers))
    outcomes: list[QuestionOutcome] = []
    score = 0
    for i, q in enumerate(_QUESTIONS):
        was_correct = answers[i] == q["correct"]
        if was_correct:
            score += 1
        outcomes.append(
            QuestionOutcome(
                id=q["id"],
                correct_index=q["correct"],
                was_correct=was_correct,
                explanation=q["explanation"],
            )
        )
    integrity_score, integrity_tier = recompute_integrity(sub.integrity)
    return ExamResult(
        passed=score >= PASS_MARK,
        score=score,
        total=len(_QUESTIONS),
        outcomes=outcomes,
        integrity_score=integrity_score,
        integrity_tier=integrity_tier,
    )
