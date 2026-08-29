// Step 3: Vehicle License Category Selection & Existing Licence Cross-Check
// Surfaces existing two-wheeler licence (MCWG) and highlights adding four-wheeler (LMV).

import { useState } from "react";

export interface ExistingLicenceInfo {
  dlNumber: string;
  classCode: string;
  className: string;
  issueDate: string;
  validUntil: string;
  status: string;
}

export interface VehicleCategory {
  id: string;
  code: string;
  name: string;
  icon: string;
  description: string;
  eligibility: string;
  popular?: boolean;
  isAddition?: boolean;
}

export const CATEGORIES: VehicleCategory[] = [
  {
    id: "lmv",
    code: "LMV",
    name: "Car (Light Motor Vehicle)",
    icon: "🚗",
    description: "Private passenger cars, sedans, SUVs, and hatchbacks.",
    eligibility: "Age 18+ • Non-transport 4-wheeler passenger vehicles",
    popular: true,
    isAddition: true,
  },
  {
    id: "mcwg",
    code: "MCWG",
    name: "Motorcycle with Gear",
    icon: "🏍️",
    description: "Geared motorcycles, sports bikes, and manual two-wheelers.",
    eligibility: "Already Active on your Sarathi Driving Licence Record",
  },
  {
    id: "mcwog",
    code: "MCWOG",
    name: "Scooter (Without Gear)",
    icon: "🛵",
    description: "Automatic scooters, mopeds, and gearless two-wheelers.",
    eligibility: "Covered under existing geared 2-wheeler endorsement",
  },
];

export function CategorySelector({
  selectedCode = "LMV",
  existingLicence = {
    dlNumber: "DL-0420210087654",
    classCode: "MCWG",
    className: "Motorcycle with Gear (Two-Wheeler)",
    issueDate: "18-May-2021",
    validUntil: "17-May-2041",
    status: "ACTIVE",
  },
  onSelect,
  onProceed,
  busy,
}: {
  selectedCode?: string;
  existingLicence?: ExistingLicenceInfo;
  onSelect: (code: string) => void;
  onProceed: () => void;
  busy: boolean;
}) {
  const [activeCode, setActiveCode] = useState(selectedCode);

  const handleChoose = (code: string) => {
    setActiveCode(code);
    onSelect(code);
  };

  return (
    <div className="category-selection-card">
      <div className="category-header">
        <div>
          <span className="badge-official">Step 3 of 9 • National Vehicle Classification &amp; Licence Endorsement</span>
          <h2 style={{ fontSize: "1.35rem", fontWeight: 700, margin: "0.4rem 0 0.2rem" }}>
            Select Licence Class to Add
          </h2>
          <p className="muted" style={{ fontSize: "0.9rem" }}>
            Our integration with the National Transport Registry (Sarathi) retrieved your verified record.
          </p>
        </div>
      </div>

      {/* Existing Licence Detection Banner */}
      {existingLicence && (
        <div style={{ margin: "1rem 0 1.25rem", padding: "1rem", background: "#f0fdf4", borderRadius: "8px", border: "1px solid #bbf7d0" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
            <div>
              <span className="chip" style={{ background: "#22c55e", color: "white", fontSize: "0.75rem", fontWeight: 700, padding: "2px 8px" }}>
                ✓ Existing Active Licence Verified
              </span>
              <h4 style={{ margin: "0.4rem 0 0.15rem", color: "#166534", fontSize: "1.05rem" }}>
                🏍️ {existingLicence.className} ({existingLicence.classCode})
              </h4>
              <p style={{ margin: 0, fontSize: "0.82rem", color: "#15803d" }}>
                DL Number: <strong>{existingLicence.dlNumber}</strong> · Valid until: <strong>{existingLicence.validUntil}</strong> · Status: <span style={{ textTransform: "uppercase", fontWeight: 700 }}>{existingLicence.status}</span>
              </p>
            </div>
            <div style={{ textAlign: "right" }}>
              <span style={{ fontSize: "0.8rem", color: "#166534", fontWeight: 600 }}>
                Transaction Type: <strong>Addition of Class (COV)</strong>
              </span>
            </div>
          </div>
          <div style={{ marginTop: "0.6rem", fontSize: "0.82rem", color: "#14532d", background: "#dcfce7", padding: "0.5rem 0.75rem", borderRadius: "6px" }}>
            💡 <strong>Fast-Track Benefit:</strong> Since you already hold a valid Two-Wheeler Licence, your fundamental road safety and signs knowledge is pre-credited under Motor Vehicles Rules. You are applying to add <strong>🚗 Car (Four-Wheeler / LMV)</strong>.
          </div>
        </div>
      )}

      <div className="category-grid">
        {CATEGORIES.map((cat) => {
          const isSelected = activeCode === cat.code;
          const isExisting = existingLicence && cat.code === existingLicence.classCode;

          return (
            <div
              key={cat.id}
              className={`category-option-card ${isSelected ? "selected" : ""} ${isExisting ? "existing-held" : ""}`}
              onClick={() => handleChoose(cat.code)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && handleChoose(cat.code)}
              style={isExisting ? { borderStyle: "dashed", opacity: 0.9, background: "#f8fafc" } : {}}
            >
              {cat.popular && <span className="category-tag-popular">✨ Applying to Add</span>}
              {isExisting && (
                <span className="category-tag-popular" style={{ background: "#166534", color: "#fff" }}>
                  ✓ Already Held
                </span>
              )}
              <div className="category-icon-wrap">{cat.icon}</div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0.4rem 0 0.2rem" }}>{cat.name}</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--ink-secondary)", flex: 1, margin: "0.3rem 0" }}>
                {cat.description}
              </p>
              <div className="category-eligibility">
                <span>{isExisting ? "✓ Already in your possession" : `ℹ️ ${cat.eligibility}`}</span>
              </div>
              <div className="category-radio-row">
                <input
                  type="radio"
                  name="vehicle_category"
                  checked={isSelected}
                  onChange={() => handleChoose(cat.code)}
                  id={`cat_${cat.id}`}
                />
                <label htmlFor={`cat_${cat.id}`} style={{ fontWeight: 600, fontSize: "0.88rem", cursor: "pointer" }}>
                  {isSelected ? `Selected to Add (${cat.code})` : `Choose ${cat.code}`}
                </label>
              </div>
            </div>
          );
        })}
      </div>

      <div className="card-footer" style={{ marginTop: "1.5rem" }}>
        <div style={{ fontSize: "0.85rem", color: "var(--ink-muted)" }}>
          Selected Endorsement: <strong style={{ color: "var(--gov-navy)" }}>{activeCode} (Four-Wheeler Car)</strong>
        </div>
        <button
          type="button"
          className="btn primary"
          onClick={onProceed}
          disabled={busy}
          style={{ padding: "0.65rem 1.4rem" }}
        >
          {busy ? "Loading Profile…" : "Proceed to Zero-Form Application →"}
        </button>
      </div>
    </div>
  );
}
