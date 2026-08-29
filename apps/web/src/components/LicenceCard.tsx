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
  onReturnHome,
}: {
  applicantId: string;
  applicationNumber: string;
  onReturnHome?: () => void;
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

  const dlNumber = deriveLicenceNumber(applicationNumber);

  return (
    <div className="licence-wrap" style={{ flexDirection: "column", alignItems: "center" }}>
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
          <span className="licence-org">UNION OF INDIA · DRIVING LICENCE (FORM 7)</span>
          <span className="licence-class">LMV</span>
        </header>
        <div className="licence-body">
          <div className="licence-photo" aria-hidden="true">
            {view?.profile.photo_url ? (
              <img
                src={view.profile.photo_url}
                alt="Citizen"
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            ) : (
              (view?.profile.name ?? "Citizen")
                .split(" ")
                .map((w) => w[0])
                .slice(0, 2)
                .join("")
            )}
          </div>
          <dl>
            <div>
              <dt>Licence no.</dt>
              <dd className="licence-no">{dlNumber}</dd>
            </div>
            <div>
              <dt>Full Name</dt>
              <dd>{view?.profile.name ?? "—"}</dd>
            </div>
            <div>
              <dt>Date of birth</dt>
              <dd>{view?.profile.dob ?? "—"}</dd>
            </div>
            <div>
              <dt>Date of Issue</dt>
              <dd>{fmt(issued)}</dd>
            </div>
            <div>
              <dt>Valid till</dt>
              <dd>{fmt(validTill)}</dd>
            </div>
            <div style={{ gridColumn: "span 2" }}>
              <dt>Authorized Vehicle Class</dt>
              <dd>LMV (Light Motor Vehicle - Motor Car)</dd>
            </div>
          </dl>
        </div>
        <footer>
          Digitally Signed by Licensing Authority • Parivahan Seva National Transport Registry
        </footer>
      </div>

      <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem", flexWrap: "wrap", justifyContent: "center" }}>
        <button
          type="button"
          className="btn primary"
          onClick={() => window.print()}
        >
          📄 Download / Print Official PDF Certificate
        </button>
        <button
          type="button"
          className="btn secondary"
          onClick={() => alert(`Digital Driving Licence (${dlNumber}) synced to your DigiLocker account.`)}
        >
          📱 Sync to DigiLocker / mParivahan
        </button>
        {onReturnHome && (
          <button type="button" className="btn secondary" onClick={onReturnHome}>
            ← Return to Citizen Homepage
          </button>
        )}
      </div>
    </div>
  );
}
