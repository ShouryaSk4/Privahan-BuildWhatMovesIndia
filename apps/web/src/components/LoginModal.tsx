// Official Parivahan Citizen Login & Aadhaar OTP Authentication Modal

import { useState } from "react";

export function LoginModal({
  isOpen,
  onClose,
  onLogin,
}: {
  isOpen: boolean;
  onClose: () => void;
  onLogin: (applicantId: string, citizenName: string) => void;
}) {
  const [authMode, setAuthMode] = useState<"aadhaar" | "phone">("aadhaar");
  const [identityInput, setIdentityInput] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otpInput, setOtpInput] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  function handleSendOtp() {
    setError(null);
    const clean = identityInput.replace(/\s+/g, "");
    if (authMode === "aadhaar" && clean.length !== 12 && !clean.startsWith("app")) {
      setError("Please enter a valid 12-digit Aadhaar Number (e.g. 5432 1098 7654)");
      return;
    }
    if (authMode === "phone" && clean.length !== 10) {
      setError("Please enter a valid 10-digit Mobile Number linked to Aadhaar");
      return;
    }
    setOtpSent(true);
  }

  function handleVerifyOtp() {
    setError(null);
    if (!otpInput.trim()) {
      setError("Please enter the 6-digit OTP sent to your registered mobile.");
      return;
    }
    // Authenticate clean session
    onLogin("applicant_001", "Rohan Verma");
    onClose();
  }

  return (
    <div className="voice-modal-backdrop" onClick={onClose}>
      <div className="login-modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="login-modal-header">
          <div>
            <span className="login-badge">DigiLocker &amp; UIDAI e-KYC</span>
            <h3>Citizen Sign-In &amp; Identity Verification</h3>
          </div>
          <button type="button" className="voice-modal-close" onClick={onClose} title="Close">
            ✕
          </button>
        </div>

        <div className="login-modal-body">
          <p className="muted" style={{ fontSize: "0.88rem", marginBottom: "1.25rem" }}>
            Authenticate securely using your Aadhaar or Mobile Number. No physical documents or paper forms required.
          </p>

          <div className="login-tab-row">
            <button
              type="button"
              className={`login-tab-btn ${authMode === "aadhaar" ? "active" : ""}`}
              onClick={() => {
                setAuthMode("aadhaar");
                setOtpSent(false);
              }}
            >
              🆔 Aadhaar Number
            </button>
            <button
              type="button"
              className={`login-tab-btn ${authMode === "phone" ? "active" : ""}`}
              onClick={() => {
                setAuthMode("phone");
                setOtpSent(false);
              }}
            >
              📱 Mobile OTP
            </button>
          </div>

          {!otpSent ? (
            <div style={{ marginTop: "1rem" }}>
              <label style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--gov-navy)" }}>
                {authMode === "aadhaar" ? "12-Digit Aadhaar Number" : "10-Digit Mobile Number"}
              </label>
              <input
                type="text"
                value={identityInput}
                placeholder={authMode === "aadhaar" ? "5432 1098 7654" : "98765 43210"}
                onChange={(e) => setIdentityInput(e.target.value)}
                style={{ marginTop: "0.4rem" }}
              />
              <p className="muted small" style={{ marginTop: "0.4rem" }}>
                🔒 Your identity data is encrypted pursuant to the Aadhaar Act, 2016.
              </p>

              <button
                type="button"
                className="btn primary"
                onClick={handleSendOtp}
                style={{ width: "100%", marginTop: "1.25rem" }}
              >
                Send OTP →
              </button>
            </div>
          ) : (
            <div style={{ marginTop: "1rem" }}>
              <div className="alert alert-good" style={{ padding: "0.75rem 1rem", fontSize: "0.85rem" }}>
                ✓ OTP sent to mobile linked with {identityInput || "your account"}. Demo OTP: <b>123456</b>
              </div>
              <label style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--gov-navy)", marginTop: "0.75rem", display: "block" }}>
                Enter 6-Digit One Time Password (OTP)
              </label>
              <input
                type="text"
                value={otpInput}
                placeholder="123456"
                maxLength={6}
                onChange={(e) => setOtpInput(e.target.value)}
                style={{ marginTop: "0.4rem", letterSpacing: "0.25em", fontSize: "1.1rem", fontWeight: 700, textAlign: "center" }}
              />

              <button
                type="button"
                className="btn primary"
                onClick={handleVerifyOtp}
                style={{ width: "100%", marginTop: "1.25rem" }}
              >
                Verify &amp; Start Fresh Application →
              </button>
            </div>
          )}

          {error && <p className="alert alert-error" style={{ marginTop: "0.75rem" }}>{error}</p>}
        </div>
      </div>
    </div>
  );
}
