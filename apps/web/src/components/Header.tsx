// National MoRTH Portal Header Component with Helpline and Citizen Context

export function Header({
  applicantId,
  applicationNumber,
  citizenName,
  onOpenVoice,
  onOpenLogin,
  onReset,
  onSwitchCitizen,
}: {
  applicantId?: string;
  applicationNumber?: string | null;
  citizenName?: string;
  onOpenVoice?: () => void;
  onOpenLogin?: () => void;
  onReset?: () => void;
  onSwitchCitizen?: () => void;
}) {
  return (
    <header>
      {/* Top National Support & Branding Strip */}
      <div className="gov-top-bar">
        <div className="gov-top-bar-inner">
          <div className="gov-branding-strip">
            <span>भारत सरकार | Government of India</span>
            <span>•</span>
            <span>सड़क परिवहन और राजमार्ग मंत्रालय (MoRTH)</span>
          </div>
          <div className="gov-branding-strip">
            <span className="gov-helpline-tag">
              📞 24x7 Citizen Helpline: 1800-180-0147 (Toll-Free)
            </span>
            <span>•</span>
            <span>Digital India Initiative</span>
          </div>
        </div>
      </div>

      {/* Main Portal Header */}
      <div className="gov-portal-header">
        <div className="gov-portal-header-inner">
          <div className="gov-title-wrap" onClick={onReset} title="Return to Citizen Portal Home">
            <svg
              className="gov-emblem-main"
              viewBox="0 0 100 100"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-label="National Emblem of India"
            >
              <circle cx="50" cy="50" r="45" stroke="#f59e0b" strokeWidth="4" fill="#0b1f41" />
              <circle cx="50" cy="50" r="16" stroke="#93c5fd" strokeWidth="2" strokeDasharray="3 3" />
              <path d="M50 20 L50 80 M20 50 L80 50 M29 29 L71 71 M29 71 L71 29" stroke="#93c5fd" strokeWidth="1.5" />
              <circle cx="50" cy="50" r="6" fill="#f59e0b" />
            </svg>
            <div className="gov-title-text">
              <h1>
                Parivahan Seva
                <span style={{ fontSize: "0.75rem", background: "rgba(255,255,255,0.15)", padding: "0.15rem 0.5rem", borderRadius: "4px" }}>
                  Official Citizen Portal
                </span>
              </h1>
              <p className="tagline">Unified Portal for Driving Licence Issuance, Road Safety &amp; Transport Services</p>
            </div>
          </div>

          <div className="gov-header-actions">
            {applicantId ? (
              <div className="citizen-context-badge">
                <span>
                  👤 <b>{citizenName || applicantId}</b>
                  {applicationNumber && <> • App #{applicationNumber}</>}
                </span>
                <button
                  type="button"
                  className="citizen-switch-btn"
                  onClick={onSwitchCitizen || onReset}
                  title="Switch citizen persona or return to portal home"
                >
                  Switch / Exit ✕
                </button>
              </div>
            ) : (
              <>
                <span className="badge-official">e-KYC Ready</span>
                {onOpenLogin && (
                  <button
                    type="button"
                    className="btn secondary"
                    onClick={onOpenLogin}
                    style={{ minHeight: "36px", padding: "0.35rem 0.85rem", fontSize: "0.82rem" }}
                  >
                    🔐 Sign-In (OTP)
                  </button>
                )}
              </>
            )}

            {onOpenVoice && (
              <button
                type="button"
                className="btn-bol-ke-apply-nav"
                onClick={onOpenVoice}
                title="बोल के अप्लाई — Voice Assistant (Hindi / English / Hinglish)"
              >
                🎙️ बोल के अप्लाई
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
