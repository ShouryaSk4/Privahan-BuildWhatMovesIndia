// Step 5: Learner License Test Mode Selection (Online AI Proctored vs RTO Center)

import { useState } from "react";

export function LLTestSelector({
  onStartOnlineTest,
  onScheduleCenterTest,
  busy,
}: {
  onStartOnlineTest: () => void;
  onScheduleCenterTest: () => void;
  busy: boolean;
}) {
  const [testMode, setTestMode] = useState<"online" | "center">("online");

  return (
    <div className="card" style={{ padding: "1.75rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <span className="badge-official">Step 5 of 9 • STALL Computerized Knowledge Test</span>
          <h2 style={{ fontSize: "1.35rem", fontWeight: 700, margin: "0.4rem 0 0.2rem" }}>
            Learner's Licence Test (Online or RTO Center)
          </h2>
          <p className="muted" style={{ fontSize: "0.9rem" }}>
            Pass the 5-question road signs, traffic regulations, and safe driving assessment to receive your digital Learner's Licence.
          </p>
        </div>
        <span className="chip status-verified">e-KYC Documents Verified ✓</span>
      </div>

      <div className="rto-choice-grid" style={{ marginTop: "1.25rem", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
        <div
          className={`rto-choice-card ${testMode === "online" ? "selected" : ""}`}
          onClick={() => setTestMode("online")}
          role="button"
          tabIndex={0}
        >
          <div style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem" }}>
            <input
              type="radio"
              name="ll_test_mode"
              checked={testMode === "online"}
              onChange={() => setTestMode("online")}
              id="mode_online"
            />
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <span style={{ fontSize: "1.3rem" }}>🎥</span>
                <label htmlFor="mode_online" style={{ fontWeight: 700, fontSize: "1rem", cursor: "pointer" }}>
                  Online AI-Proctored Test (At Home)
                </label>
              </div>
              <span className="chip" style={{ background: "#dcfce7", color: "#166534", marginTop: "0.4rem" }}>
                ⚡ Instant · Zero RTO Visit
              </span>
              <p style={{ fontSize: "0.84rem", color: "var(--ink-secondary)", margin: "0.5rem 0 0" }}>
                Take the test directly on your browser via Aadhaar face authentication and AI proctoring. Requires camera &amp; mic.
              </p>
            </div>
          </div>
        </div>

        <div
          className={`rto-choice-card ${testMode === "center" ? "selected" : ""}`}
          onClick={() => setTestMode("center")}
          role="button"
          tabIndex={0}
        >
          <div style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem" }}>
            <input
              type="radio"
              name="ll_test_mode"
              checked={testMode === "center"}
              onChange={() => setTestMode("center")}
              id="mode_center"
            />
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <span style={{ fontSize: "1.3rem" }}>🏛️</span>
                <label htmlFor="mode_center" style={{ fontWeight: 700, fontSize: "1rem", cursor: "pointer" }}>
                  RTO Center Computerized Lab
                </label>
              </div>
              <span className="chip" style={{ marginTop: "0.4rem" }}>In-Person Touchscreen</span>
              <p style={{ fontSize: "0.84rem", color: "var(--ink-secondary)", margin: "0.5rem 0 0" }}>
                Visit your designated RTO computerized testing center. Staff assistance available for first-time digital test takers.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="card-footer" style={{ marginTop: "1.5rem" }}>
        <div style={{ fontSize: "0.85rem", color: "var(--ink-muted)" }}>
          Test Format: <strong>5 Multiple Choice Questions</strong> • Passing Score: <strong>60% (3/5)</strong>
        </div>
        <button
          type="button"
          className="btn primary"
          onClick={testMode === "online" ? onStartOnlineTest : onScheduleCenterTest}
          disabled={busy}
          style={{ padding: "0.65rem 1.4rem" }}
        >
          {busy ? "Loading…" : testMode === "online" ? "Start Online AI-Proctored Test →" : "Schedule RTO Test Slot →"}
        </button>
      </div>
    </div>
  );
}
