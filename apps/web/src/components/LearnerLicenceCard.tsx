// Step 6: Digital Learner's Licence Certificate (Form 3 CMVR)

export function LearnerLicenceCard({
  applicantId,
  applicationNumber,
  citizenName,
  vehicleClass = "LMV",
  onProceedToPractice,
  busy,
}: {
  applicantId: string;
  applicationNumber?: string;
  citizenName?: string;
  vehicleClass?: string;
  onProceedToPractice: () => void;
  busy: boolean;
}) {
  const issueDate = new Date().toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
  const validUntil = new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
  const llNumber = `LL-DL01-${applicationNumber ? applicationNumber.slice(-6) : "202601"}`;

  return (
    <div className="card" style={{ padding: "1.75rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <span className="badge-official">Step 6 of 9 • Ministry of Road Transport &amp; Highways</span>
          <h2 style={{ fontSize: "1.35rem", fontWeight: 700, margin: "0.4rem 0 0.2rem" }}>
            Learner's Licence Issued (Form 3)
          </h2>
          <p className="muted" style={{ fontSize: "0.9rem" }}>
            Congratulations! You have passed the computerized test. Your digital Learner's Licence is active.
          </p>
        </div>
        <span className="chip status-verified">✓ Digital Permit Active</span>
      </div>

      <div className="ll-certificate-card" style={{ marginTop: "1.25rem" }}>
        <div className="ll-card-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <span style={{ fontSize: "1.8rem" }}>🇮🇳</span>
            <div>
              <div style={{ fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase" }}>
                Government of National Capital Territory of Delhi
              </div>
              <div style={{ fontSize: "0.95rem", fontWeight: 800, color: "#1e3a8a" }}>
                FORM 3 — LEARNER'S LICENCE
              </div>
            </div>
          </div>
          <div className="ll-qr-mock">
            <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "#1e3a8a" }}>QR AUTH</span>
          </div>
        </div>

        <div className="ll-card-body">
          <div className="ll-detail-grid">
            <div>
              <span className="ll-label">Licence Number:</span>
              <span className="ll-value">{llNumber}</span>
            </div>
            <div>
              <span className="ll-label">Application Ref:</span>
              <span className="ll-value">{applicationNumber || applicantId}</span>
            </div>
            <div>
              <span className="ll-label">Holder Name:</span>
              <span className="ll-value">{citizenName || "Rohan Verma"}</span>
            </div>
            <div>
              <span className="ll-label">Vehicle Class:</span>
              <span className="ll-value" style={{ color: "#1e3a8a", fontWeight: 800 }}>{vehicleClass} (Car / Light Motor Vehicle)</span>
            </div>
            <div>
              <span className="ll-label">Date of Issue:</span>
              <span className="ll-value">{issueDate}</span>
            </div>
            <div>
              <span className="ll-label">Valid Until:</span>
              <span className="ll-value" style={{ color: "#166534", fontWeight: 700 }}>{validUntil} (6 Months)</span>
            </div>
          </div>
        </div>

        <div className="ll-card-footer">
          <span style={{ fontSize: "0.78rem", color: "#475569" }}>
            🔒 Digitally signed via Aadhaar e-Sign · Syncs automatically to DigiLocker &amp; mParivahan
          </span>
          <button
            type="button"
            className="btn secondary"
            style={{ fontSize: "0.8rem", padding: "0.3rem 0.75rem" }}
            onClick={() => alert("Digital LL downloaded to your device as PDF.")}
          >
            📥 Download Form 3 PDF
          </button>
        </div>
      </div>

      <div className="card-footer" style={{ marginTop: "1.5rem" }}>
        <div style={{ fontSize: "0.85rem", color: "var(--ink-muted)" }}>
          Next: <strong>30-Day Mandatory Practice Window</strong> with AI Driving Safety Academy
        </div>
        <button
          type="button"
          className="btn primary"
          onClick={onProceedToPractice}
          disabled={busy}
          style={{ padding: "0.65rem 1.4rem" }}
        >
          {busy ? "Loading Slots…" : "Select Appointment Date & Time for Driving Test →"}
        </button>
      </div>
    </div>
  );
}
