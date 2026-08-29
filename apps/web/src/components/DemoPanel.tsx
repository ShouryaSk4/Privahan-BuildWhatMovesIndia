// Dev-only RTO simulator: drives the mock government side of Module 5 so the
// whole journey can be walked without real Sarathi access, then asks Module 2
// to sync. Hidden behind a toggle; not part of the citizen experience.

import { useState } from "react";
import { demoRtoApi, journeyApi, type JourneyState } from "../api/client";

const CHECKPOINTS = [
  "reverse_parking",
  "8_turn",
  "hill_start",
  "clutch_control",
  "steering",
];

export function DemoPanel({
  state,
  onUpdate,
  onReset,
}: {
  state: JourneyState;
  onUpdate: (s: JourneyState) => void;
  onReset?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [checkpoint, setCheckpoint] = useState(CHECKPOINTS[0]);
  const [error, setError] = useState<string | null>(null);
  const appNo = state.application_number;

  async function run(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
      onUpdate(await journeyApi.sync(state.applicant_id));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function handleReset() {
    setError(null);
    try {
      const resetState = await journeyApi.reset(state.applicant_id);
      onUpdate(resetState);
      if (onReset) onReset();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  if (!open) {
    return (
      <button className="btn ghost demo-toggle" onClick={() => setOpen(true)}>
        RTO simulator (dev)
      </button>
    );
  }

  return (
    <aside className="demo card" aria-label="RTO simulator — development only">
      <header className="row space-between">
        <strong>RTO simulator</strong>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            type="button"
            className="btn ghost"
            style={{ fontSize: "0.75rem", color: "#dc2626" }}
            onClick={handleReset}
            title="Reset this applicant journey back to start"
          >
            ↺ Reset Journey
          </button>
          <button className="btn ghost" onClick={() => setOpen(false)}>✕</button>
        </div>
      </header>
      <p className="muted">
        Stands in for the government side (mock Module 5) until real Sarathi access exists.
      </p>
      {!appNo && <p className="muted">Submit an application first.</p>}
      {appNo && (
        <div className="demo-actions">
          <button
            className="btn secondary"
            onClick={() => run(() => demoRtoApi.verifyDocuments(appNo))}
            disabled={state.current_stage !== "ll_application_submitted"}
          >
            RTO verifies documents
          </button>
          <button
            className="btn secondary"
            onClick={() => run(() => demoRtoApi.reportTestResult(appNo, "ll", true))}
            disabled={state.current_stage !== "ll_documents_verified"}
          >
            Pass the LL test
          </button>
          <div className="row">
            <select
              value={checkpoint}
              onChange={(e) => setCheckpoint(e.target.value)}
              aria-label="Failed checkpoint"
            >
              {CHECKPOINTS.map((c) => (
                <option key={c} value={c}>{c.replaceAll("_", " ")}</option>
              ))}
            </select>
            <button
              className="btn secondary"
              onClick={() => run(() => demoRtoApi.reportTestResult(appNo, "dl", false, checkpoint))}
              disabled={state.current_stage !== "dl_test_booked"}
            >
              Fail DL test
            </button>
          </div>
          <button
            className="btn secondary"
            onClick={() => run(() => demoRtoApi.reportTestResult(appNo, "dl", true))}
            disabled={state.current_stage !== "dl_test_booked"}
          >
            Pass DL test
          </button>
        </div>
      )}
      {error && <p className="alert alert-error">{error}</p>}
    </aside>
  );
}
