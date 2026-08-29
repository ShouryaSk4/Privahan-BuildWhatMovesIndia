// Dedicated Step: Select Driving Test Appointment Date & Time Slot (ADTT)

import { useState } from "react";
import type { TestSlot } from "../api/client";

export function SlotBookingPicker({
  slots,
  onConfirmBooking,
  onBack,
  busy,
}: {
  slots: TestSlot[];
  onConfirmBooking: (slotId: string, slotLabel: string) => void;
  onBack?: () => void;
  busy: boolean;
}) {
  const [selectedSlotId, setSelectedSlotId] = useState<string>(
    slots.length > 0 ? slots[0].slot_id : ""
  );

  const selectedSlot = slots.find((s) => s.slot_id === selectedSlotId);

  const formatSlotLabel = (s: TestSlot) => {
    return new Date(s.starts_at).toLocaleString("en-IN", {
      weekday: "short",
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  return (
    <div className="card" style={{ padding: "1.75rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <span className="badge-official">Step 7 of 9 • Automated Driving Test Track (ADTT)</span>
          <h2 style={{ fontSize: "1.35rem", fontWeight: 700, margin: "0.4rem 0 0.2rem" }}>
            Select Driving Test Appointment Date &amp; Time
          </h2>
          <p className="muted" style={{ fontSize: "0.9rem" }}>
            Choose the appointment date and time slot for your physical driving evaluation at RTO Mall Road Automated Track (DL01).
          </p>
        </div>
        <span className="chip status-verified">Learner's Licence Active ✓</span>
      </div>

      <div className="alert alert-good" style={{ marginTop: "1rem" }}>
        <strong>📅 30-Day Mandatory Skill Acquisition Practice Window:</strong>
        <p style={{ marginTop: "0.25rem", fontSize: "0.86rem" }}>
          Selecting your test slot locks in your evaluation date. During the period leading up to your appointment, you will have
          access to the AI Driving Safety Academy video curriculum to practice your maneuvers.
        </p>
      </div>

      <div style={{ marginTop: "1.25rem" }}>
        <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--gov-navy)", marginBottom: "0.75rem" }}>
          Available Appointment Slots (ADTT Track 1 — DL01):
        </h3>

        <div className="rto-choice-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
          {slots.map((s) => {
            const isSelected = selectedSlotId === s.slot_id;
            const label = formatSlotLabel(s);
            return (
              <div
                key={s.slot_id}
                className={`rto-choice-card ${isSelected ? "selected" : ""}`}
                onClick={() => setSelectedSlotId(s.slot_id)}
                role="button"
                tabIndex={0}
              >
                <div style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem" }}>
                  <input
                    type="radio"
                    name="slot_choice"
                    checked={isSelected}
                    onChange={() => setSelectedSlotId(s.slot_id)}
                    id={`slot_${s.slot_id}`}
                  />
                  <div style={{ flex: 1 }}>
                    <label htmlFor={`slot_${s.slot_id}`} style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--gov-navy)", cursor: "pointer", display: "block" }}>
                      {label}
                    </label>
                    <div style={{ display: "flex", gap: "0.4rem", marginTop: "0.35rem", alignItems: "center" }}>
                      <span className="chip" style={{ fontSize: "0.72rem", background: "#f0fdf4", color: "#15803d" }}>
                        ⚡ {s.capacity_left} Slots Available
                      </span>
                      <span style={{ fontSize: "0.72rem", color: "var(--ink-muted)" }}>
                        · Track 1 (Sensors)
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card-footer" style={{ marginTop: "1.75rem" }}>
        {onBack && (
          <button type="button" className="btn secondary" onClick={onBack} disabled={busy}>
            ← Back to Learner's Licence
          </button>
        )}
        <div style={{ fontSize: "0.85rem", color: "var(--ink-muted)" }}>
          Selected Appointment: <strong>{selectedSlot ? formatSlotLabel(selectedSlot) : "None"}</strong>
        </div>
        <button
          type="button"
          className="btn primary"
          onClick={() => selectedSlot && onConfirmBooking(selectedSlot.slot_id, formatSlotLabel(selectedSlot))}
          disabled={busy || !selectedSlotId}
          style={{ padding: "0.65rem 1.4rem" }}
        >
          {busy ? "Confirming Appointment…" : "Confirm Appointment & Start Practice →"}
        </button>
      </div>
    </div>
  );
}
