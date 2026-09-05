// Dev-only RTO simulator. It stands in for the government reporting a physical
// driving-test result — routed through the token-checked journey service, never
// the raw /gov endpoints (which now require a service token the browser lacks).
// Document verification and the LL pass are handled server-side (auto-verify on
// apply; the STALL exam is graded on the server), so only the DL result remains.

import { useState } from "react";
import { journeyApi, type JourneyState } from "../api/client";

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
  const atDlTest = state.current_stage === "dl_test_booked";

  async function run(action: () => Promise<JourneyState>) {
    setError(null);
    try {
      onUpdate(await action());
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
        Stands in for the RTO reporting the physical driving-test result. Document
        verification and the learner's test are handled on the server.
      </p>
      {!appNo && <p className="muted">Submit an application first.</p>}
      {appNo && (
        <div className="demo-actions">
          {!atDlTest && (
            <p className="muted" style={{ fontSize: "0.8rem" }}>
              Available once a driving-test slot is booked.
            </p>
          )}
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
              onClick={() => run(() => journeyApi.simulateDlResult(state.applicant_id, false, checkpoint))}
              disabled={!atDlTest}
            >
              Fail DL test
            </button>
          </div>
          <button
            className="btn secondary"
            onClick={() => run(() => journeyApi.simulateDlResult(state.applicant_id, true))}
            disabled={!atDlTest}
          >
            Pass DL test
          </button>
        </div>
      )}
      {error && <p className="alert alert-error">{error}</p>}
    </aside>
  );
}
