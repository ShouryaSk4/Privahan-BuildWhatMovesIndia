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
  const [rtoChoice, setRtoChoice] = useState<string>("");
  const [confirmed, setConfirmed] = useState(false);

  // Module 2 owns the advisory-vs-blocking rule (§5.3); Module 1 just renders it.
  const blockingMismatches = view.blocking_mismatches ?? [];
  const blocked = !view.clear_to_submit;
  const needsRtoChoice = addressesDisagree && rtoChoice === "";
  const gpsChoice = view.gps_rto_choice ?? profile.gps_suggested_rto ?? "";
  const aadhaarChoice = view.aadhaar_rto_choice ?? "aadhaar_jurisdiction";

  return (
    <section className="card" aria-label="Review your details">
      <h2>Review your details</h2>
      <p className="muted">
        Fetched via {profile.source === "digilocker_aadhaar" ? "DigiLocker / Aadhaar e-KYC" : profile.source}. You
        don't fill a form — you check one.
      </p>
      <p className="zero-form-stat" role="note">
        Fields you typed: <b>0</b> · Fields we fetched: <b>4</b>
      </p>
      <dl className="profile-grid">
        <div><dt>Name</dt><dd>{profile.name}</dd></div>
        <div><dt>Date of birth</dt><dd>{profile.dob}</dd></div>
        <div><dt>Address</dt><dd>{profile.address}</dd></div>
        <div><dt>Photo</dt><dd>On file from Aadhaar</dd></div>
      </dl>

      {blocked && (
        <div className="alert alert-error" role="alert">
          <strong>Fix this before applying — it would be rejected later:</strong>
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
        <div className="alert alert-warn">
          <strong>Two different RTOs apply to you.</strong>
          <p>
            Your current location suggests <b>{profile.gps_suggested_rto}</b>, but your
            Aadhaar-registered address is <b>{profile.aadhaar_registered_address}</b>. Choose
            where to apply:
          </p>
          <label>
            <input
              type="radio"
              name="rto"
              value={gpsChoice}
              checked={rtoChoice === gpsChoice}
              onChange={() => setRtoChoice(gpsChoice)}
            />
            Near me now — {profile.gps_suggested_rto}
          </label>
          <label>
            <input
              type="radio"
              name="rto"
              value={aadhaarChoice}
              checked={rtoChoice === aadhaarChoice}
              onChange={() => setRtoChoice(aadhaarChoice)}
            />
            My Aadhaar jurisdiction — {profile.aadhaar_registered_address}
          </label>
        </div>
      )}

      {!blocked && (
        <label className="confirm-check">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          These details are correct and mine.
        </label>
      )}

      <div className="row">
        <button className="btn secondary" onClick={onCancel} disabled={submitting}>
          Back
        </button>
        {!blocked && (
          <button
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
