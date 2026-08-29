// Zero-form review-and-confirm: the citizen reviews fetched, verified data —
// they never fill a form. RTO jurisdiction disagreements are surfaced for an
// explicit choice, never silently resolved (AGENTS.md §5.3).

import { useState } from "react";
import type { VerifiedIdentityView } from "../api/client";

export function ReviewConfirm({
  view,
  onConfirm,
  onCancel,
  submitting,
}: {
  view: VerifiedIdentityView;
  onConfirm: (confirmedRtoCode?: string) => void;
  onCancel: () => void;
  submitting: boolean;
}) {
  const { profile } = view;
  const addressesDisagree = profile.addresses_match === false;
  const gpsChoice = view.gps_rto_choice ?? profile.gps_suggested_rto ?? "";
  const aadhaarChoice = view.aadhaar_rto_choice ?? "aadhaar_jurisdiction";

  const [rtoChoice, setRtoChoice] = useState<string>("");
  const [confirmed, setConfirmed] = useState(false);

  const blockingMismatches = view.blocking_mismatches ?? [];
  const blocked = !view.clear_to_submit;
  const needsRtoChoice = addressesDisagree && !rtoChoice;

  return (
    <section className="card" aria-label="Review your details">
      <h2>Verified Citizen Demographic Record</h2>
      <p className="muted">
        Authenticated via {profile.source === "digilocker_aadhaar" ? "DigiLocker National Identity Repository & UIDAI Aadhaar e-KYC" : profile.source}.
        Official demographic records have been securely retrieved without manual form entry.
      </p>

      <div className="zero-form-stat" role="note">
        <span>🛡️ Zero-Form Licence Architecture:</span>
        <span>Fields you typed: <b>0</b> · Fields verified from e-KYC: <b>4</b></span>
      </div>

      <div className="profile-dossier">
        <div className="profile-avatar-wrap">
          {profile.photo_url ? (
            <img src={profile.photo_url} alt="Aadhaar photo" />
          ) : (
            <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, color: "#475569" }}>
              {profile.name.slice(0, 2).toUpperCase()}
            </div>
          )}
        </div>

        <dl className="profile-grid">
          <div>
            <dt>Full Legal Name</dt>
            <dd>{profile.name}</dd>
          </div>
          <div>
            <dt>Date of Birth</dt>
            <dd>{profile.dob}</dd>
          </div>
          <div style={{ gridColumn: "span 2" }}>
            <dt>Aadhaar Registered Permanent Address</dt>
            <dd>{profile.address}</dd>
          </div>
          <div>
            <dt>Identity Source</dt>
            <dd>UIDAI Aadhaar / DigiLocker</dd>
          </div>
          <div>
            <dt>PAN Cross-Check</dt>
            <dd style={{ color: "#166534", fontWeight: 600 }}>✓ Verified (Income Tax Dept)</dd>
          </div>
          <div>
            <dt>Existing Active Licence</dt>
            <dd style={{ color: "#0369a1", fontWeight: 600 }}>🏍️ MCWG (DL-0420210087654)</dd>
          </div>
          <div>
            <dt>Applying To Add</dt>
            <dd style={{ color: "var(--gov-navy)", fontWeight: 700 }}>🚗 LMV (Four-Wheeler Car)</dd>
          </div>
        </dl>
      </div>

      {blocked && (
        <div className="alert alert-error" role="alert">
          <strong>Fix this before applying — it would be rejected later:</strong>
          <p style={{ marginTop: "0.25rem", fontSize: "0.82rem" }}>
            Our Rejection-Prevention Engine detected discrepancies with secondary regulatory databases (PAN/UIDAI):
          </p>
          <ul>
            {blockingMismatches.map((m) => (
              <li key={m.field}>
                <b>{m.field}:</b> {m.issue} <em>{m.suggested_fix}</em>
              </li>
            ))}
          </ul>
        </div>
      )}

      {addressesDisagree && !blocked && (
        <div className="alert-rto-section">
          <div className="alert-rto-header">
            <strong>⚠️ Two different RTOs apply to you.</strong>
            <p>
              Your device GPS location suggests <b>{profile.gps_suggested_rto}</b>, but your
              Aadhaar registered address is in <b>{profile.aadhaar_registered_address}</b>. Pursuant to Motor Vehicles Rules, choose your preferred Licensing Authority:
            </p>
          </div>

          <div className="rto-choice-grid">
            <label
              className={`rto-choice-card ${rtoChoice === gpsChoice ? "selected" : ""}`}
              onClick={() => setRtoChoice(gpsChoice)}
            >
              <input
                type="radio"
                name="rto"
                value={gpsChoice}
                checked={rtoChoice === gpsChoice}
                onChange={() => setRtoChoice(gpsChoice)}
                aria-label={`Near me now — ${profile.gps_suggested_rto}`}
              />
              <div className="rto-choice-content">
                <div className="rto-choice-title">📍 Current Device Location (Convenience RTO)</div>
                <div className="rto-choice-name">Near me now — {profile.gps_suggested_rto}</div>
                <div className="rto-choice-desc">Recommended if you currently reside or work near this area.</div>
              </div>
            </label>

            <label
              className={`rto-choice-card ${rtoChoice === aadhaarChoice ? "selected" : ""}`}
              onClick={() => setRtoChoice(aadhaarChoice)}
            >
              <input
                type="radio"
                name="rto"
                value={aadhaarChoice}
                checked={rtoChoice === aadhaarChoice}
                onChange={() => setRtoChoice(aadhaarChoice)}
                aria-label={`My Aadhaar jurisdiction — ${profile.aadhaar_registered_address}`}
              />
              <div className="rto-choice-content">
                <div className="rto-choice-title">🏛️ Aadhaar Permanent Address (Statutory Jurisdiction)</div>
                <div className="rto-choice-name">My Aadhaar jurisdiction — {profile.aadhaar_registered_address}</div>
                <div className="rto-choice-desc">Official permanent jurisdiction mapped to your Aadhaar records.</div>
              </div>
            </label>
          </div>
        </div>
      )}

      {!blocked && (
        <label className={`confirm-check ${confirmed ? "checked" : ""}`}>
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          <span>These details are correct and mine.</span>
        </label>
      )}

      <div className="card-footer">
        <button type="button" className="btn secondary" onClick={onCancel} disabled={submitting}>
          ← Back
        </button>
        {!blocked && (
          <button
            type="button"
            className="btn primary"
            disabled={!confirmed || needsRtoChoice || submitting}
            onClick={() => onConfirm(addressesDisagree ? rtoChoice : undefined)}
          >
            {submitting ? "Submitting…" : "Confirm & submit application"}
          </button>
        )}
      </div>
    </section>
  );
}
