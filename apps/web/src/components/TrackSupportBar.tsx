// Bottom Track & Support Strip (Always Available at Every Step)

import { useState } from "react";

export function TrackSupportBar({
  applicantId,
  applicationNumber,
  currentStage,
  onOpenVoice,
}: {
  applicantId: string;
  applicationNumber?: string;
  currentStage: string;
  onOpenVoice: () => void;
}) {
  const [activeModal, setActiveModal] = useState<string | null>(null);

  const getStageTitle = (s: string) => {
    switch (s) {
      case "no_licence":
        return "Application Initiated";
      case "ll_application_submitted":
        return "Application Submitted";
      case "ll_documents_verified":
      case "ll_test_scheduled":
        return "Documents Verified · Test Ready";
      case "ll_issued":
        return "Learner's Licence Issued";
      case "practice_window":
        return "In 30-Day Practice Window";
      case "dl_test_booked":
        return "Driving Test Slot Confirmed";
      case "dl_test_result_pass":
      case "dl_issued":
        return "Driving Licence Issued (Form 7)";
      default:
        return "Active Session";
    }
  };

  return (
    <>
      <footer className="track-support-bar" aria-label="Track & Support Strip">
        <div className="track-support-container">
          <div className="track-support-label">
            <span>🛡️</span>
            <strong>TRACK &amp; SUPPORT</strong>
            <span style={{ fontSize: "0.75rem", color: "var(--ink-muted)" }}>(Live Status)</span>
          </div>

          <div className="track-support-links">
            <button
              type="button"
              className="track-support-btn"
              onClick={() => setActiveModal("status")}
            >
              📄 Application Tracking
            </button>
            <button
              type="button"
              className="track-support-btn"
              onClick={() => setActiveModal("docs")}
            >
              📋 Document Status
            </button>
            <button
              type="button"
              className="track-support-btn"
              onClick={() => setActiveModal("appointment")}
            >
              📅 Appointment History
            </button>
            <button
              type="button"
              className="track-support-btn highlight"
              onClick={onOpenVoice}
            >
              🎙️ AI Assistant / Chatbot (24x7)
            </button>
          </div>
        </div>
      </footer>

      {activeModal && (
        <div className="login-modal-overlay" onClick={() => setActiveModal(null)}>
          <div className="login-modal-panel" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "560px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "0.75rem", marginBottom: "1rem" }}>
              <h3 style={{ fontSize: "1.15rem", fontWeight: 700, margin: 0, color: "var(--gov-navy)" }}>
                {activeModal === "status" && "📄 Application Status Tracking"}
                {activeModal === "docs" && "📋 Verified Document Repository"}
                {activeModal === "appointment" && "📅 Appointment & Track Booking"}
              </h3>
              <button type="button" className="btn ghost" onClick={() => setActiveModal(null)}>✕</button>
            </div>

            {activeModal === "status" && (
              <div style={{ fontSize: "0.9rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                <div><strong>Application Reference:</strong> <code>{applicationNumber || applicantId}</code></div>
                <div><strong>Current Stage:</strong> <span className="chip status-verified">{getStageTitle(currentStage)}</span></div>
                <div><strong>Processing RTO:</strong> DL01 (Mall Road RTO, New Delhi)</div>
                <div><strong>Identity Authentication:</strong> DigiLocker Aadhaar e-KYC (Instant Verified)</div>
              </div>
            )}

            {activeModal === "docs" && (
              <div style={{ fontSize: "0.88rem", display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", padding: "0.5rem", background: "#f8fafc", borderRadius: "6px" }}>
                  <span>✓ <strong>Aadhaar e-KYC</strong> (Identity, Photo &amp; Address)</span>
                  <span className="chip" style={{ background: "#dcfce7", color: "#166534" }}>Auto-Verified</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", padding: "0.5rem", background: "#f8fafc", borderRadius: "6px" }}>
                  <span>✓ <strong>Form 1 Physical Fitness</strong> (Self-Declaration)</span>
                  <span className="chip" style={{ background: "#dcfce7", color: "#166534" }}>Digitally Signed</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", padding: "0.5rem", background: "#f8fafc", borderRadius: "6px" }}>
                  <span>✓ <strong>Age Eligibility (18+ Proof)</strong></span>
                  <span className="chip" style={{ background: "#dcfce7", color: "#166534" }}>Verified</span>
                </div>
              </div>
            )}

            {activeModal === "appointment" && (
              <div style={{ fontSize: "0.9rem" }}>
                <p style={{ color: "var(--ink-secondary)" }}>
                  {currentStage === "dl_test_booked"
                    ? "Your Automated Driving Test Track slot is booked at ADTT Track 1 (Mall Road RTO). Please carry your original LL."
                    : "No pending in-person physical visits. Computerized LL test is conducted online from home."}
                </p>
              </div>
            )}

            <div style={{ marginTop: "1.25rem", textAlign: "right" }}>
              <button type="button" className="btn primary" onClick={() => setActiveModal(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
