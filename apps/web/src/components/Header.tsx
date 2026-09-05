// National MoRTH portal header: slim utility bar (helpline, accessibility,
// language) + compact branding row. The original portal's header buries key
// info under dense text; this one keeps one job per row.

import { useEffect, useState } from "react";

import { setLang, useLang, useT } from "../i18n";

type FontScale = "sm" | "md" | "lg";

const PREF_KEY = "parivahan_a11y_v1";

function loadPrefs(): { fontScale: FontScale; highContrast: boolean } {
  try {
    const raw = localStorage.getItem(PREF_KEY);
    if (raw) return JSON.parse(raw) as { fontScale: FontScale; highContrast: boolean };
  } catch {
    /* fall through to defaults */
  }
  return { fontScale: "md", highContrast: false };
}

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
  const t = useT();
  const lang = useLang();
  const [prefs, setPrefs] = useState(loadPrefs);

  // Apply accessibility preferences to the document root so every screen —
  // not just this component — respects them.
  useEffect(() => {
    document.documentElement.dataset.fontScale = prefs.fontScale;
    document.documentElement.classList.toggle("hc", prefs.highContrast);
    try {
      localStorage.setItem(PREF_KEY, JSON.stringify(prefs));
    } catch {
      /* storage unavailable — prefs apply for this visit only */
    }
  }, [prefs]);

  return (
    <header>
      <a className="skip-link" href="#main-content">
        {t.skipToContent}
      </a>

      {/* Utility bar: identity left; helpline + accessibility + language right */}
      <div className="gov-top-bar">
        <div className="gov-top-bar-inner">
          <div className="gov-branding-strip">
            <span>भारत सरकार | Government of India</span>
            <span className="gov-top-sep" aria-hidden="true">
              •
            </span>
            <span className="gov-ministry">{t.ministry}</span>
          </div>
          <div className="gov-utility-strip">
            <a className="gov-helpline-tag" href="tel:18001800147">
              📞 {t.helpline}
            </a>
            <span className="gov-top-sep" aria-hidden="true">
              |
            </span>
            <div className="a11y-controls" role="group" aria-label="Accessibility">
              <button
                type="button"
                onClick={() => setPrefs((p) => ({ ...p, fontScale: "sm" }))}
                aria-label={t.fontSmaller}
                aria-pressed={prefs.fontScale === "sm"}
              >
                A−
              </button>
              <button
                type="button"
                onClick={() => setPrefs((p) => ({ ...p, fontScale: "md" }))}
                aria-label={t.fontReset}
                aria-pressed={prefs.fontScale === "md"}
              >
                A
              </button>
              <button
                type="button"
                onClick={() => setPrefs((p) => ({ ...p, fontScale: "lg" }))}
                aria-label={t.fontLarger}
                aria-pressed={prefs.fontScale === "lg"}
              >
                A+
              </button>
              <button
                type="button"
                className="a11y-contrast"
                onClick={() => setPrefs((p) => ({ ...p, highContrast: !p.highContrast }))}
                aria-label={t.highContrast}
                aria-pressed={prefs.highContrast}
                title={t.highContrast}
              >
                ◐
              </button>
            </div>
            <span className="gov-top-sep" aria-hidden="true">
              |
            </span>
            <div className="lang-toggle" role="group" aria-label="Language / भाषा">
              <button
                type="button"
                onClick={() => setLang("en")}
                aria-pressed={lang === "en"}
                className={lang === "en" ? "active" : ""}
              >
                EN
              </button>
              <button
                type="button"
                onClick={() => setLang("hi")}
                aria-pressed={lang === "hi"}
                className={lang === "hi" ? "active" : ""}
              >
                हिंदी
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Branding row: compact emblem + name; actions on the right */}
      <div className="gov-portal-header">
        <div className="gov-portal-header-inner">
          <div
            className="gov-title-wrap"
            onClick={onReset}
            title="Parivahan Seva — Home"
            role="link"
            tabIndex={0}
            onKeyDown={(e) => e.key === "Enter" && onReset?.()}
          >
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
              <h1>Parivahan Seva</h1>
              <p className="tagline">{t.tagline}</p>
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
                  {t.switchExit} ✕
                </button>
              </div>
            ) : (
              <>
                <span className="badge-official">{t.ekycReady}</span>
                {onOpenLogin && (
                  <button
                    type="button"
                    className="btn secondary btn-signin"
                    onClick={onOpenLogin}
                  >
                    🔐 {t.signIn}
                  </button>
                )}
              </>
            )}

            {onOpenVoice && (
              <button
                type="button"
                className="btn-bol-ke-apply-nav"
                onClick={onOpenVoice}
                title={t.voiceTitle}
              >
                {t.voiceButton}
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
