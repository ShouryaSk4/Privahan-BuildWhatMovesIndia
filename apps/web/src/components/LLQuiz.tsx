// The learner's licence test, in the app — Delhi's Aadhaar path allows the
// online test from home, so the demo makes it a real interaction instead of a
// simulator button. Scoring logic is pure and unit-tested.

import { useState } from "react";

export type QuizQuestion = {
  id: string;
  prompt: string;
  options: string[];
  correct: number; // index into options
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
  },
  {
    id: "school",
    prompt: "Passing a school zone, the safe speed is:",
    options: ["60 km/h", "40 km/h", "25 km/h"],
    correct: 2,
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
  busy,
}: {
  onResult: (passed: boolean, score: number) => void;
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
      <p className="muted">
        Three questions, answer {PASS_MARK} correctly. This is the online test — from your
        home, no RTO visit.
      </p>
      {QUESTIONS.map((q, qi) => (
        <fieldset key={q.id} className="quiz-q" disabled={result?.passed || busy}>
          <legend>
            {qi + 1}. {q.prompt}
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
              {opt}
            </label>
          ))}
        </fieldset>
      ))}
      {result === null ? (
        <button className="btn primary" disabled={!allAnswered || busy} onClick={submit}>
          Submit answers
        </button>
      ) : result.passed ? (
        <p className="alert alert-good" role="status">
          ✅ {result.score}/{QUESTIONS.length} — passed! Issuing your learner's licence…
        </p>
      ) : (
        <div className="alert alert-warn" role="status">
          <p>
            {result.score}/{QUESTIONS.length} — not quite. The correct answers are now
            highlighted; take a look and try again. No fee, no penalty.
          </p>
          <button className="btn secondary" onClick={retry}>
            Try again
          </button>
        </div>
      )}
    </div>
  );
}
