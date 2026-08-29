// The memorable ending: the issued licence rendered as a card, built from the
// same verified data that powered the zero-form application.

import { useEffect, useState } from "react";
import { journeyApi, type VerifiedIdentityView } from "../api/client";

export function deriveLicenceNumber(applicationNumber: string, rto = "DL07"): string {
  const serial = applicationNumber.replace(/\D/g, "").slice(-9).padStart(9, "0");
  return `${rto} ${serial.slice(0, 4)} ${serial.slice(4)}`;
}

const CONFETTI_COLORS = ["#1e4b9e", "#e8a13a", "#1a7f4e", "#c8102e", "#6e9be0"];

export function LicenceCard({
  applicantId,
  applicationNumber,
}: {
  applicantId: string;
  applicationNumber: string;
}) {
  const [view, setView] = useState<VerifiedIdentityView | null>(null);
  useEffect(() => {
    journeyApi.verifiedProfile(applicantId).then(setView).catch(() => setView(null));
  }, [applicantId]);

  const issued = new Date();
  const validTill = new Date(issued);
  validTill.setFullYear(validTill.getFullYear() + 20);
  const fmt = (d: Date) =>
    d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });

  return (
    <div className="licence-wrap print-zone">
      <div className="confetti" aria-hidden="true">
        {Array.from({ length: 24 }, (_, i) => (
          <span
            key={i}
            style={{
              left: `${(i * 41) % 100}%`,
              animationDelay: `${(i % 8) * 0.22}s`,
              background: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
            }}
          />
        ))}
      </div>
      <div className="licence-card" role="img" aria-label="Your driving licence">
        <header>
          <span className="licence-org">UNION OF INDIA · DRIVING LICENCE</span>
          <span className="licence-class">LMV</span>
        </header>
        <div className="licence-body">
          <div className="licence-photo" aria-hidden="true">
            {(view?.profile.name ?? "Citizen")
              .split(" ")
              .map((w) => w[0])
              .slice(0, 2)
              .join("")}
          </div>
          <dl>
            <div>
              <dt>Licence no.</dt>
              <dd className="licence-no">{deriveLicenceNumber(applicationNumber)}</dd>
            </div>
            <div>
              <dt>Name</dt>
              <dd>{view?.profile.name ?? "—"}</dd>
            </div>
            <div>
              <dt>Date of birth</dt>
              <dd>{view?.profile.dob ?? "—"}</dd>
            </div>
            <div>
              <dt>Issued</dt>
              <dd>{fmt(issued)}</dd>
            </div>
            <div>
              <dt>Valid till</dt>
              <dd>{fmt(validTill)}</dd>
            </div>
          </dl>
        </div>
        <footer>Issued digitally via Parivahan Seva · Zero forms · One visit</footer>
      </div>
      <button className="btn secondary print-hide" onClick={() => window.print()}>
        🖨️ Print / save licence as PDF
      </button>
    </div>
  );
}
