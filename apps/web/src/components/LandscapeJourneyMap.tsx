// Journey progression map. The original portal shows all nine steps at once
// with no "you are here" — overwhelming and directionless. This renders a
// compact progress strip (current step, what's next, % complete) and keeps
// the full milestone road one tap away.

import { useState } from "react";

import { fmt, useT } from "../i18n";

export type JourneyStepKey =
  | "intent"
  | "login"
  | "category"
  | "application"
  | "ll_test"
  | "ll_issued"
  | "practice"
  | "dl_booking"
  | "dl_test";

const STEP_KEYS: JourneyStepKey[] = [
  "intent",
  "login",
  "category",
  "application",
  "ll_test",
  "ll_issued",
  "practice",
  "dl_booking",
  "dl_test",
];

const STEP_ICONS = ["🌐", "🆔", "🚗", "📋", "💻", "📜", "🎯", "📅", "🏆"];

export function getActiveStepKey(stage: string, reviewOpen: boolean, categorySelected: boolean): JourneyStepKey {
  if (reviewOpen) return "application";
  switch (stage) {
    case "no_licence":
      return categorySelected ? "application" : "category";
    case "ll_application_submitted":
      return "application";
    case "ll_documents_verified":
    case "ll_test_scheduled":
      return "ll_test";
    case "ll_issued":
      return "ll_issued";
    case "practice_window":
      return "practice";
    case "dl_test_booked":
      return "dl_booking";
    case "dl_test_result_fail":
      return "practice";
    case "dl_test_result_pass":
    case "dl_issued":
      return "dl_test";
    default:
      return "intent";
  }
}

const EXPAND_KEY = "parivahan_journeymap_expanded";

export function LandscapeJourneyMap({ currentStep }: { currentStep: JourneyStepKey }) {
  const t = useT();
  const [expanded, setExpanded] = useState(() => {
    try {
      return localStorage.getItem(EXPAND_KEY) === "1";
    } catch {
      return false;
    }
  });

  const currentIdx = Math.max(0, STEP_KEYS.indexOf(currentStep));
  const total = STEP_KEYS.length;
  const current = t.steps[currentIdx];
  const next = currentIdx + 1 < total ? t.steps[currentIdx + 1] : null;
  const pct = Math.round(((currentIdx + 1) / total) * 100);

  function toggle() {
    setExpanded((v) => {
      try {
        localStorage.setItem(EXPAND_KEY, v ? "0" : "1");
      } catch {
        /* fine */
      }
      return !v;
    });
  }

  return (
    <nav className="journey-progress" aria-label="Citizen journey progress">
      <div className="journey-progress-row">
        <span className="you-are-here">📍 {t.youAreHere}</span>
        <div className="journey-progress-text">
          <strong>
            {fmt(t.stepProgress, { n: currentIdx + 1, total })}: {current.title}
          </strong>
          <span className="journey-progress-next">
            {next ? `${t.nextWord}: ${next.title}` : `🏆 ${t.journeyDone}`}
          </span>
        </div>
        <div
          className="journey-progress-track"
          role="progressbar"
          aria-valuemin={1}
          aria-valuemax={total}
          aria-valuenow={currentIdx + 1}
          aria-label={fmt(t.stepProgress, { n: currentIdx + 1, total })}
        >
          <div className="journey-progress-fill" style={{ width: `${pct}%` }} />
        </div>
        <button type="button" className="journey-progress-toggle" onClick={toggle} aria-expanded={expanded}>
          {expanded ? t.hideAllSteps : t.showAllSteps}
        </button>
      </div>

      {expanded && (
        <div className="landscape-journey-container">
          <div className="landscape-journey-scroll">
            <ol className="landscape-journey-steps">
              {t.steps.map((step, idx) => {
                const isDone = idx < currentIdx;
                const isCurrent = idx === currentIdx;
                return (
                  <li
                    key={STEP_KEYS[idx]}
                    className={`landscape-journey-step ${isDone ? "done" : ""} ${isCurrent ? "current" : ""}`}
                    aria-current={isCurrent ? "step" : undefined}
                  >
                    <div className="landscape-step-marker">{isDone ? "✓" : idx + 1}</div>
                    <div className="landscape-step-content">
                      <span className="landscape-step-title">
                        <span aria-hidden="true">{STEP_ICONS[idx]}</span> {step.title}
                      </span>
                      <span className="landscape-step-sub">{step.subtitle}</span>
                    </div>
                    {idx < total - 1 && <div className="landscape-step-connector" />}
                  </li>
                );
              })}
            </ol>
          </div>
        </div>
      )}
    </nav>
  );
}
