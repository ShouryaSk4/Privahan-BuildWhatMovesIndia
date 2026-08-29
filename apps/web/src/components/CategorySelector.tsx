// Step 3: Vehicle License Category Selection (Landscape-First Desktop Component)

import { useState } from "react";

export interface VehicleCategory {
  id: string;
  code: string;
  name: string;
  icon: string;
  description: string;
  eligibility: string;
  popular?: boolean;
}

export const CATEGORIES: VehicleCategory[] = [
  {
    id: "lmv",
    code: "LMV",
    name: "Car (Light Motor Vehicle)",
    icon: "🚗",
    description: "Private passenger cars, sedans, SUVs, and hatchbacks.",
    eligibility: "Age 18+ • Valid for non-transport passenger vehicles",
    popular: true,
  },
  {
    id: "mcwg",
    code: "MCWG",
    name: "Motorcycle with Gear",
    icon: "🏍️",
    description: "Geared motorcycles, sports bikes, and manual two-wheelers.",
    eligibility: "Age 18+ • Covers all geared 2-wheelers across India",
  },
  {
    id: "mcwog",
    code: "MCWOG",
    name: "Scooter (Without Gear)",
    icon: "🛵",
    description: "Automatic scooters, mopeds, and gearless two-wheelers.",
    eligibility: "Age 16+ (with parental consent) or 18+",
  },
];

export function CategorySelector({
  selectedCode = "LMV",
  onSelect,
  onProceed,
  busy,
}: {
  selectedCode?: string;
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
          <span className="badge-official">Step 3 of 9 • National Vehicle Classification</span>
          <h2 style={{ fontSize: "1.35rem", fontWeight: 700, margin: "0.4rem 0 0.2rem" }}>
            Select Driving Licence Category
          </h2>
          <p className="muted" style={{ fontSize: "0.9rem" }}>
            Choose the vehicle class you intend to obtain a learner's and permanent driving licence for.
          </p>
        </div>
      </div>

      <div className="category-grid">
        {CATEGORIES.map((cat) => {
          const isSelected = activeCode === cat.code;
          return (
            <div
              key={cat.id}
              className={`category-option-card ${isSelected ? "selected" : ""}`}
              onClick={() => handleChoose(cat.code)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && handleChoose(cat.code)}
            >
              {cat.popular && <span className="category-tag-popular">Most Popular</span>}
              <div className="category-icon-wrap">{cat.icon}</div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0.4rem 0 0.2rem" }}>{cat.name}</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--ink-secondary)", flex: 1, margin: "0.3rem 0" }}>
                {cat.description}
              </p>
              <div className="category-eligibility">
                <span>ℹ️ {cat.eligibility}</span>
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
                  {isSelected ? `Selected (${cat.code})` : `Choose ${cat.code}`}
                </label>
              </div>
            </div>
          );
        })}
      </div>

      <div className="card-footer" style={{ marginTop: "1.5rem" }}>
        <div style={{ fontSize: "0.85rem", color: "var(--ink-muted)" }}>
          Selected Class: <strong style={{ color: "var(--gov-navy)" }}>{activeCode}</strong> (Statutory Form 2 Auto-Filled via e-KYC)
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
