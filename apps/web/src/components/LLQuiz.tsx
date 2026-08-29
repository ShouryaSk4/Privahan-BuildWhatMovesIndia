// The learner's licence test, in the app — Delhi's Aadhaar path allows the
// online test from home, so the demo makes it a real interaction instead of a
// simulator button. Scoring logic is pure and unit-tested.

import { useState } from "react";

export type QuizQuestion = {
  id: string;
  prompt: string;
  options: string[];
  correct: number; // index into options
  explanation: string;
};

export const QUESTIONS: QuizQuestion[] = [
  {
    id: "triangle",
    prompt: "A red-bordered triangle sign with an exclamation mark means:",
    options: [
      "General caution — slow down and stay alert",
      "Compulsory horn zone",
      "No parking beyond this point",
    ],
    correct: 0,
    explanation: "Triangular signs are cautionary/warning signs indicating potential road hazards ahead.",
  },
  {
    id: "zebra",
    prompt: "A pedestrian is waiting at a zebra crossing. You should:",
    options: [
      "Sound the horn and keep moving",
      "Stop and let them cross",
      "Speed up to clear the crossing first",
    ],
    correct: 1,
    explanation: "Pedestrians have legal right of way at marked pedestrian and zebra crossings.",
  },
  {
    id: "school",
    prompt: "Passing a school zone, the safe speed is:",
    options: ["60 km/h", "40 km/h", "25 km/h"],
    correct: 2,
    explanation: "Standard regulatory speed limit in school and hospital safety zones is 25 km/h.",
  },
];

export const PASS_MARK = 2;

export function scoreQuiz(answers: (number | null)[]): number {
  return QUESTIONS.reduce(
    (score, q, i) => (answers[i] === q.correct ? score + 1 : score),
    0,
  );
}

export function LLQuiz({
  onResult,
  onBack,
  busy,
}: {
  onResult: (passed: boolean, score: number) => void;
  onBack?: () => void;
  busy: boolean;
}) {
  const [answers, setAnswers] = useState<(number | null)[]>(
    QUESTIONS.map(() => null),
  );
  const [result, setResult] = useState<{ passed: boolean; score: number } | null>(null);
  const allAnswered = answers.every((a) => a !== null);

  function submit() {
    const score = scoreQuiz(answers);
    const passed = score >= PASS_MARK;
    setResult({ passed, score });
    if (passed) onResult(true, score);
  }

  function retry() {
    setAnswers(QUESTIONS.map(() => null));
    setResult(null);
  }

  return (
    <div className="quiz" aria-label="Learner's licence test">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.75rem", flexWrap: "wrap", gap: "0.5rem" }}>
        <p className="muted" style={{ margin: 0, fontSize: "0.92rem" }}>
          <b>Screen Test for Aid of Learner's Licence (STALL):</b> 3 questions. Minimum passing score is {PASS_MARK}/{QUESTIONS.length}.
          Conducted digitally at home pursuant to MoRTH Contactless Citizen Services.
        </p>
      </div>

      {QUESTIONS.map((q, qi) => (
        <fieldset key={q.id} className="quiz-q" disabled={result?.passed || busy}>
          <legend>
            Question {qi + 1} of {QUESTIONS.length} — {q.prompt}
          </legend>
          {q.options.map((opt, oi) => (
            <label key={oi} className={result && oi === q.correct ? "quiz-correct" : ""}>
              <input
                type="radio"
                name={q.id}
                checked={answers[qi] === oi}
                onChange={() =>
                  setAnswers((a) => a.map((v, i) => (i === qi ? oi : v)))
                }
              />
              <span>{opt}</span>
            </label>
          ))}
          {result && !result.passed && (
            <p style={{ fontSize: "0.8rem", color: "var(--gov-emerald)", marginTop: "0.4rem", fontWeight: 600 }}>
              💡 Rule explanation: {q.explanation}
            </p>
          )}
        </fieldset>
      ))}

      <div className="row" style={{ marginTop: "1rem" }}>
        {onBack && (
          <button type="button" className="btn secondary" onClick={onBack} disabled={busy}>
            ← Back to Application Overview
          </button>
        )}

        {result === null ? (
          <button className="btn primary" disabled={!allAnswered || busy} onClick={submit}>
            {busy ? "Evaluating…" : "Submit answers"}
          </button>
        ) : result.passed ? (
          <div className="alert alert-good" role="status" style={{ width: "100%" }}>
            <strong>✅ {result.score}/{QUESTIONS.length} — passed!</strong> Issuing your official Learner's Licence Form 3 digitally…
          </div>
        ) : (
          <div className="alert alert-warn" role="status" style={{ width: "100%" }}>
            <p>
              <b>Result: {result.score}/{QUESTIONS.length}</b> — The passing threshold is {PASS_MARK}/{QUESTIONS.length}.
              The correct answers and statutory rules are now highlighted above. No fee, no penalty.
            </p>
            <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem" }}>
              <button className="btn secondary" onClick={retry}>
                Try again
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
