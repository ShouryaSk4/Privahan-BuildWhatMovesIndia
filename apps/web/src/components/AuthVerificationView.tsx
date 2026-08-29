// Step 2: Citizen Mobile & DigiLocker e-KYC Verification View
// Asks for citizen mobile number, handles 6-digit OTP verification,
// and fetches Aadhaar, PAN, and existing 2-wheeler licence records.

import { useState } from "react";

export interface VerifiedCitizenData {
  applicantId: string;
  phone: string;
  aadhaarNumber: string;
  name: string;
  dob: string;
  panNumber: string;
  address: string;
  existingLicence?: {
    dlNumber: string;
    classCode: string;
    className: string;
    issueDate: string;
    validUntil: string;
    status: string;
  };
}

export function AuthVerificationView({
  onVerified,
  onBack,
  busy,
}: {
  onVerified: (data: VerifiedCitizenData) => void;
  onBack: () => void;
  busy?: boolean;
}) {
  const [phoneNumber, setPhoneNumber] = useState("9876543210");
  const [aadhaarInput, setAadhaarInput] = useState("5432 1098 7654");
  const [otpSent, setOtpSent] = useState(false);
  const [otpValue, setOtpValue] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendOtp = () => {
    setError(null);
    const cleanPhone = phoneNumber.replace(/\D/g, "");
    if (cleanPhone.length < 10) {
      setError("Please enter a valid 10-digit mobile number linked to your Aadhaar.");
      return;
    }
    setOtpSent(true);
    setOtpValue("123456"); // Pre-populate demo OTP for smooth presentation
  };

  const handleVerify = () => {
    setError(null);
    if (!otpValue.trim() || otpValue.trim().length !== 6) {
      setError("Please enter the 6-digit OTP sent to your registered mobile.");
      return;
    }

    setIsVerifying(true);
    setTimeout(() => {
      setIsVerifying(false);
      // Construct verified dossier with active 2-wheeler licence in Sarathi registry
      onVerified({
        applicantId: "applicant_001",
        phone: phoneNumber,
        aadhaarNumber: "XXXXXXXX7654",
        name: "Rohan Verma",
        dob: "2002-03-14",
        panNumber: "ABCPV1234F",
        address: "12 Patel Nagar, New Delhi, 110008",
        existingLicence: {
          dlNumber: "DL-0420210087654",
          classCode: "MCWG",
          className: "Motor Cycle with Gear (Two-Wheeler)",
          issueDate: "18-May-2021",
          validUntil: "17-May-2041",
          status: "ACTIVE",
        },
      });
    }, 600);
  };

  return (
    <div className="card" style={{ maxWidth: "680px", margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <span className="badge-official">Step 2 of 9 • Identity &amp; e-KYC Verification</span>
          <h2 style={{ fontSize: "1.35rem", fontWeight: 700, margin: "0.4rem 0 0.2rem" }}>
            Citizen Authentication &amp; Document Fetch
          </h2>
          <p className="muted" style={{ fontSize: "0.88rem" }}>
            Enter your mobile number to authenticate via DigiLocker. We will securely retrieve your Aadhaar demographic details, PAN cross-checks, and existing transport licence records.
          </p>
        </div>
        <span className="chip status-verified">DigiLocker / UIDAI Gateway</span>
      </div>

      <div style={{ marginTop: "1.25rem", padding: "1rem", background: "#f8fafc", borderRadius: "8px", border: "1px solid var(--line)" }}>
        {!otpSent ? (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
              <div>
                <label style={{ fontSize: "0.84rem", fontWeight: 700, color: "var(--gov-navy)" }}>
                  📱 Aadhaar-Linked Mobile Number:
                </label>
                <div style={{ display: "flex", alignItems: "center", marginTop: "0.35rem" }}>
                  <span style={{ padding: "0.6rem 0.75rem", background: "#e2e8f0", border: "1px solid #cbd5e1", borderRight: "none", borderRadius: "6px 0 0 6px", fontSize: "0.9rem", fontWeight: 600 }}>
                    +91
                  </span>
                  <input
                    type="tel"
                    value={phoneNumber}
                    maxLength={10}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="98765 43210"
                    style={{ borderRadius: "0 6px 6px 0", flex: 1 }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: "0.84rem", fontWeight: 700, color: "var(--gov-navy)" }}>
                  🆔 Aadhaar Number (UIDAI):
                </label>
                <input
                  type="text"
                  value={aadhaarInput}
                  onChange={(e) => setAadhaarInput(e.target.value)}
                  placeholder="5432 1098 7654"
                  style={{ marginTop: "0.35rem", width: "100%" }}
                />
              </div>
            </div>

            <p className="muted small" style={{ marginTop: "0.75rem" }}>
              🔒 <strong>Statutory Privacy Protection:</strong> Data fetched directly from UIDAI / DigiLocker encrypted pursuant to Aadhaar Act 2016. No manual document upload or paper verification needed.
            </p>

            <div style={{ marginTop: "1.25rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <button type="button" className="btn secondary" onClick={onBack} disabled={busy}>
                ← Back to Services
              </button>
              <button type="button" className="btn primary" onClick={handleSendOtp} disabled={busy}>
                Send OTP via DigiLocker →
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="alert alert-good" style={{ padding: "0.75rem 1rem", fontSize: "0.85rem", marginBottom: "1rem" }}>
              ✓ <strong>OTP Sent:</strong> 6-digit one-time password dispatched to mobile <strong>+91 {phoneNumber}</strong>.
            </div>

            <div style={{ maxWidth: "320px", margin: "0 auto", textAlign: "center" }}>
              <label style={{ fontSize: "0.86rem", fontWeight: 700, color: "var(--gov-navy)", display: "block", marginBottom: "0.4rem" }}>
                Enter 6-Digit Verification OTP:
              </label>
              <input
                type="text"
                value={otpValue}
                maxLength={6}
                onChange={(e) => setOtpValue(e.target.value)}
                placeholder="123456"
                style={{
                  textAlign: "center",
                  fontSize: "1.3rem",
                  letterSpacing: "0.35em",
                  fontWeight: 800,
                  padding: "0.6rem",
                  width: "100%",
                  color: "var(--gov-navy)",
                }}
              />
              <div style={{ marginTop: "0.4rem", fontSize: "0.78rem", color: "var(--ink-muted)" }}>
                Demo auto-fill: <code>123456</code> · <button type="button" style={{ border: "none", background: "none", color: "var(--gov-blue)", cursor: "pointer", textDecoration: "underline" }} onClick={() => setOtpValue("123456")}>Quick Fill</button>
              </div>
            </div>

            <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <button
                type="button"
                className="btn secondary"
                onClick={() => setOtpSent(false)}
                disabled={isVerifying || busy}
              >
                ← Change Mobile Number
              </button>
              <button
                type="button"
                className="btn primary"
                onClick={handleVerify}
                disabled={isVerifying || busy}
                style={{ minWidth: "160px" }}
              >
                {isVerifying ? "Fetching e-KYC Records…" : "Verify OTP & Fetch Records →"}
              </button>
            </div>
          </div>
        )}

        {error && <p className="alert alert-error" style={{ marginTop: "1rem" }}>{error}</p>}
      </div>

      <div style={{ marginTop: "1rem", display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.75rem" }}>
        <div style={{ padding: "0.6rem 0.8rem", background: "#f1f5f9", borderRadius: "6px", fontSize: "0.78rem" }}>
          <strong>🆔 Aadhaar e-KYC</strong>
          <p style={{ margin: "0.2rem 0 0", color: "var(--ink-secondary)" }}>Name, DOB, Photo &amp; Jurisdiction</p>
        </div>
        <div style={{ padding: "0.6rem 0.8rem", background: "#f1f5f9", borderRadius: "6px", fontSize: "0.78rem" }}>
          <strong>🛡️ PAN Cross-Check</strong>
          <p style={{ margin: "0.2rem 0 0", color: "var(--ink-secondary)" }}>Rejection prevention verification</p>
        </div>
        <div style={{ padding: "0.6rem 0.8rem", background: "#f1f5f9", borderRadius: "6px", fontSize: "0.78rem" }}>
          <strong>🏍️ Sarathi DL Registry</strong>
          <p style={{ margin: "0.2rem 0 0", color: "var(--ink-secondary)" }}>Existing Two-Wheeler Licence lookup</p>
        </div>
      </div>
    </div>
  );
}
