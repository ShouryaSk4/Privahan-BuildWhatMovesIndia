import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  clearSession,
  getStoredSession,
  journeyApi,
  startSession,
  type JourneyState,
  type TestSlot,
  type VerifiedIdentityView,
} from "./api/client";
import { AcademyWidget } from "./components/AcademyWidget";
import { AuthVerificationView, type VerifiedCitizenData } from "./components/AuthVerificationView";
import { CategorySelector } from "./components/CategorySelector";
import { DemoPanel } from "./components/DemoPanel";
import { Header } from "./components/Header";
import { LandscapeJourneyMap, getActiveStepKey } from "./components/LandscapeJourneyMap";
import { LearnerLicenceCard } from "./components/LearnerLicenceCard";
import { LicenceCard } from "./components/LicenceCard";
import { LLQuiz } from "./components/LLQuiz";
import { LLTestSelector } from "./components/LLTestSelector";
import { LoginModal } from "./components/LoginModal";
import { NavigationBar } from "./components/NavigationBar";
import { PracticeAcademyView } from "./components/PracticeAcademyView";
import { ReviewConfirm } from "./components/ReviewConfirm";
import { SlotBookingPicker } from "./components/SlotBookingPicker";
import { TrackSupportBar } from "./components/TrackSupportBar";
import { VoiceModal } from "./components/VoiceModal";
import { useT } from "./i18n";

const APPLICANT_ID_PATTERN = /^[A-Za-z0-9_-]{4,32}$/;

const DEMO_PERSONAS = [
  {
    id: "applicant_001",
    name: "Rohan Verma",
    location: "Bengaluru, KA",
    tag: "Standard Clean Journey • Full Eligibility",
    desc: "Aadhaar address & GPS location match. Clear identity cross-check.",
  },
  {
    id: "applicant_student",
    name: "Priya Sharma",
    location: "Lucknow (Aadhaar) / Bengaluru (GPS)",
    tag: "Inter-State Mover • Jurisdiction Choice",
    desc: "Surfaces statutory choice between legal Aadhaar RTO and convenience RTO.",
  },
  {
    id: "applicant_mismatch",
    name: "Vikram Singh Chauhan",
    location: "Delhi, DL",
    tag: "Rejection-Prevention Advisory",
    desc: "Aadhaar vs PAN name discrepancy detected with statutory resolution guidance.",
  },
];

function describeError(e: unknown): string {
  if (e instanceof ApiError) {
    if (typeof e.detail === "string") return e.detail;
    if (e.detail && typeof e.detail === "object" && "message" in e.detail) {
      return String((e.detail as { message: unknown }).message);
    }
  }
  return e instanceof Error ? e.message : String(e);
}

function getStepInfo(stage: string): string {
  switch (stage) {
    case "no_licence":
      return "Step 3/4: License Class & Zero-Form Dossier";
    case "ll_application_submitted":
      return "Step 4: Application Submitted";
    case "ll_documents_verified":
    case "ll_test_scheduled":
      return "Step 5: Online/Center Learner's Test (STALL)";
    case "ll_issued":
      return "Step 6: Digital Learner's Licence Issued";
    case "practice_window":
      return "Step 7: 30-Day Practice & Road Safety Academy";
    case "dl_test_booked":
      return "Step 8: Automated Track Test Scheduled (ADTT)";
    case "dl_test_result_fail":
      return "Step 7: Maneuver Remediation & Retest";
    case "dl_test_result_pass":
    case "dl_issued":
      return "Step 9: Form 7 Permanent Driving Licence";
    default:
      return "Citizen Application Journey";
  }
}

export default function App() {
  const t = useT();
  const [applicantId, setApplicantId] = useState("");
  const [idInput, setIdInput] = useState("applicant_001");
  const [idError, setIdError] = useState<string | null>(null);
  const [state, setState] = useState<JourneyState | null>(null);
  const [review, setReview] = useState<VerifiedIdentityView | null>(null);
  const [slots, setSlots] = useState<TestSlot[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);

  // Landscape-First Step Progression State
  const [authFlowActive, setAuthFlowActive] = useState(false);
  const [verifiedData, setVerifiedData] = useState<VerifiedCitizenData | null>(null);
  const [selectedCategory, setSelectedCategory] = useState("LMV");
  const [categoryConfirmed, setCategoryConfirmed] = useState(false);
  const [onlineTestActive, setOnlineTestActive] = useState(false);
  const [bookedSlotLabel, setBookedSlotLabel] = useState("29 Sep 2026 at 10:00 AM");
  // "Your application never dies": a stored session offers one-click resume.
  const [storedSession] = useState(getStoredSession);
  const [stageToast, setStageToast] = useState<string | null>(null);
  const lastStageRef = useRef<string | null>(null);

  function resumeJourney() {
    const stored = getStoredSession();
    if (stored) enter(stored.applicantId, false);
  }

  // Push, not pull: while the journey waits on the government side, poll sync
  // quietly and announce stage changes — no more "check for updates" clicking
  // (the original portal's captcha-gated tracking page, politely reproduced).
  const WAITING_STAGES = ["ll_application_submitted", "dl_test_booked"];
  useEffect(() => {
    lastStageRef.current = state?.current_stage ?? null;
    if (!applicantId || !state || !WAITING_STAGES.includes(state.current_stage)) return;
    const timer = setInterval(async () => {
      try {
        const fresh = await journeyApi.sync(applicantId);
        if (fresh.current_stage !== lastStageRef.current) {
          lastStageRef.current = fresh.current_stage;
          setState(fresh);
          setStageToast(fresh.next_action?.label ?? "Your application moved forward.");
          window.setTimeout(() => setStageToast(null), 7000);
        }
      } catch {
        /* transient — the next tick retries */
      }
    }, 10000);
    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [applicantId, state?.current_stage]);

  // Journey state is loaded by enter() after the session token is minted; no
  // effect refetch here, which would race the token on first entry.

  async function act<T>(fn: () => Promise<T>): Promise<T | undefined> {
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      setError(describeError(e));
      return undefined;
    } finally {
      setBusy(false);
    }
  }

  function enter(id?: string, resetFirst = true) {
    const targetId = (id ?? idInput).trim();
    if (!APPLICANT_ID_PATTERN.test(targetId)) {
      setIdError("ID must be 4–32 letters, numbers, or underscores (e.g. applicant_001)");
      return;
    }
    setIdError(null);
    setReview(null);
    setSlots(null);
    setError(null);
    setCategoryConfirmed(false);
    setOnlineTestActive(false);

    // Mint the session token BEFORE any journey call, then load state. Every
    // /journey request is ownership-checked, so the token must exist first.
    act(async () => {
      await startSession(targetId);
      const fresh = resetFirst
        ? await journeyApi.reset(targetId)
        : await journeyApi.get(targetId);
      setApplicantId(targetId);
      setState(fresh);
    });
  }

  function resetToLanding() {
    clearSession();
    setApplicantId("");
    setState(null);
    setReview(null);
    setSlots(null);
    setError(null);
    setAuthFlowActive(false);
    setVerifiedData(null);
    setCategoryConfirmed(false);
    setOnlineTestActive(false);
  }

  const activePersona = DEMO_PERSONAS.find((p) => p.id === applicantId);

  // =========================================================================
  // Screen A2: Step 2 — Citizen Mobile & DigiLocker e-KYC Verification
  // =========================================================================
  if (!applicantId && authFlowActive) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <Header onOpenVoice={() => setVoiceOpen(true)} onReset={resetToLanding} />
        <LandscapeJourneyMap currentStep="login" />
        <NavigationBar
          breadcrumbs={[
            { label: "Citizen Home", onClick: resetToLanding },
            { label: "Step 2: e-KYC & Mobile Auth", active: true },
          ]}
          onBack={resetToLanding}
          backLabel="← Return to Citizen Homepage"
          stepInfo="Step 2 of 9: Citizen Verification & Document Retrieval"
        />
        <main className="shell" id="main-content">
          <AuthVerificationView
            busy={busy}
            onBack={resetToLanding}
            onVerified={(data) => {
              setVerifiedData(data);
              setAuthFlowActive(false);
              setIdInput(data.applicantId);
              enter(data.applicantId, true);
            }}
          />
        </main>
        <TrackSupportBar
          applicantId="portal_visitor"
          currentStage="no_licence"
          onOpenVoice={() => setVoiceOpen(true)}
        />
        <VoiceModal
          applicantId="applicant_001"
          isOpen={voiceOpen}
          onClose={() => setVoiceOpen(false)}
        />
      </div>
    );
  }

  // =========================================================================
  // Screen A: Task-First Citizen Homepage (Step 1: Portal Landing)
  // =========================================================================
  if (!applicantId) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <Header onOpenVoice={() => setVoiceOpen(true)} onOpenLogin={() => setLoginOpen(true)} />

        <LandscapeJourneyMap currentStep="intent" />

        <main className="shell" id="main-content">
          {/* Hero Section: gantry board with copy left, rule-guaranteed stats right */}
          <section className="task-first-hero" aria-label="Parivahan Seva Overview">
            <div className="hero-grid">
              <div className="hero-copy">
                <p className="hero-eyebrow">{t.heroEyebrow}</p>
                <h1>{t.heroHeading}</h1>
                <p className="sub">{t.heroSub}</p>
              </div>
              <aside className="hero-stats" aria-label={t.statsTitle}>
                <div className="hero-stats-title">{t.statsTitle}</div>
                <dl>
                  <div className="hero-stat">
                    <dt>₹1,350</dt>
                    <dd>{t.statCost}</dd>
                  </div>
                  <div className="hero-stat">
                    <dt>21</dt>
                    <dd>{t.statDays}</dd>
                  </div>
                  <div className="hero-stat">
                    <dt>1</dt>
                    <dd>{t.statVisits}</dd>
                  </div>
                </dl>
                <p className="hero-stats-note">{t.statsNote}</p>
              </aside>
            </div>

            {/* Task-First Service Cards */}
            <div className="task-cards-grid">
              <div
                className="task-card featured"
                role="button"
                tabIndex={0}
                onClick={() => setAuthFlowActive(true)}
                onKeyDown={(e) => e.key === "Enter" && setAuthFlowActive(true)}
              >
                <div>
                  <div className="task-card-badge">{t.recommendedBadge}</div>
                  <div className="task-card-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="2" y="5" width="20" height="14" rx="2.5" />
                      <circle cx="8" cy="11" r="2.2" />
                      <path d="M4.8 17c.6-1.9 1.8-2.8 3.2-2.8s2.6.9 3.2 2.8" />
                      <path d="M14 9.5h6M14 12.5h6M14 15.5h3.5" />
                    </svg>
                  </div>
                  <h3 className="task-card-title">{t.card1Title}</h3>
                  <ul className="task-card-points">
                    {t.card1Points.map((pt) => (
                      <li key={pt}>{pt}</li>
                    ))}
                  </ul>
                </div>
                <span className="task-card-action">{t.card1Cta} →</span>
              </div>

              <div
                className="task-card"
                role="button"
                tabIndex={0}
                onClick={() => {
                  setIdInput("applicant_student");
                  enter("applicant_student", true);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    setIdInput("applicant_student");
                    enter("applicant_student", true);
                  }
                }}
              >
                <div>
                  <div className="task-card-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 21s-6.5-5.4-6.5-10.2a6.5 6.5 0 1 1 13 0C18.5 15.6 12 21 12 21Z" />
                      <circle cx="12" cy="10.5" r="2.4" />
                    </svg>
                  </div>
                  <h3 className="task-card-title">{t.card2Title}</h3>
                  <ul className="task-card-points">
                    {t.card2Points.map((pt) => (
                      <li key={pt}>{pt}</li>
                    ))}
                  </ul>
                </div>
                <span className="task-card-action">{t.card2Cta} →</span>
              </div>

              <div
                className="task-card"
                role="button"
                tabIndex={0}
                onClick={() => {
                  setIdInput("applicant_mismatch");
                  enter("applicant_mismatch", true);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    setIdInput("applicant_mismatch");
                    enter("applicant_mismatch", true);
                  }
                }}
              >
                <div>
                  <div className="task-card-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 3l7.5 3v5.2c0 4.6-3.1 7.6-7.5 9.8-4.4-2.2-7.5-5.2-7.5-9.8V6l7.5-3Z" />
                      <path d="M8.8 12.2l2.2 2.2 4.2-4.6" />
                    </svg>
                  </div>
                  <h3 className="task-card-title">{t.card3Title}</h3>
                  <ul className="task-card-points">
                    {t.card3Points.map((pt) => (
                      <li key={pt}>{pt}</li>
                    ))}
                  </ul>
                </div>
                <span className="task-card-action">{t.card3Cta} →</span>
              </div>

              <div
                className="task-card"
                role="button"
                tabIndex={0}
                onClick={() => setVoiceOpen(true)}
                onKeyDown={(e) => e.key === "Enter" && setVoiceOpen(true)}
              >
                <div>
                  <div className="task-card-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="9" y="3" width="6" height="11" rx="3" />
                      <path d="M5.5 11.5a6.5 6.5 0 0 0 13 0" />
                      <path d="M12 18v3M8.5 21h7" />
                    </svg>
                  </div>
                  <h3 className="task-card-title">{t.card4Title}</h3>
                  <ul className="task-card-points">
                    {t.card4Points.map((pt) => (
                      <li key={pt}>{pt}</li>
                    ))}
                  </ul>
                </div>
                <span className="task-card-action">{t.card4Cta} →</span>
              </div>
            </div>
          </section>

          {/* Quick Sign-In / Demo Persona Selector */}
          <section className="card-signin" aria-label="Sign in to application">
            {storedSession && !applicantId && (
              <div className="resume-banner" role="note">
                <div>
                  <strong>{t.welcomeBack}</strong> <code>{storedSession.applicantId}</code>{" "}
                  {t.resumeBody}
                </div>
                <button type="button" className="btn primary" onClick={resumeJourney} disabled={busy}>
                  {t.resumeCta}
                </button>
              </div>
            )}
            <h2>{t.signinHeading}</h2>
            <p className="muted" style={{ fontSize: "0.9rem" }}>
              {t.signinSub}
            </p>

            <div className="persona-preset-selector">
              <div className="persona-preset-title">{t.personaTitle}</div>
              <div className="persona-chips">
                {DEMO_PERSONAS.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    className={`persona-chip-btn ${idInput === p.id ? "active" : ""}`}
                    onClick={() => {
                      setIdInput(p.id);
                      enter(p.id, true);
                    }}
                  >
                    <div>
                      <div className="persona-chip-name">{p.name}</div>
                      <div className="persona-chip-tag">{p.tag} • {p.location}</div>
                    </div>
                    <span style={{ fontSize: "0.85rem", color: "var(--gov-blue)", fontWeight: 800 }}>{t.startFresh}</span>
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginTop: "1.25rem" }}>
              <label htmlFor="applicant" style={{ fontSize: "0.88rem", fontWeight: 700, color: "var(--gov-navy)" }}>
                {t.customIdLabel}
              </label>
              <div style={{ display: "flex", gap: "0.65rem", marginTop: "0.4rem", flexWrap: "wrap" }}>
                <input
                  id="applicant"
                  type="text"
                  value={idInput}
                  placeholder="e.g. applicant_001"
                  onChange={(e) => setIdInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && enter(undefined, false)}
                  style={{ flex: 1, minWidth: "16rem" }}
                />
                <button className="btn primary" onClick={() => enter(undefined, false)} style={{ whiteSpace: "nowrap" }}>
                  {t.continueCta}
                </button>
              </div>
              <p className="muted small" style={{ marginTop: "0.4rem" }}>
                {t.formatHint} <code>applicant_001</code>)
              </p>
            </div>
            {idError && <p className="alert alert-error">{idError}</p>}
          </section>
        </main>

        <TrackSupportBar
          applicantId="portal_visitor"
          currentStage="no_licence"
          onOpenVoice={() => setVoiceOpen(true)}
        />

        <VoiceModal
          applicantId={idInput || "applicant_001"}
          isOpen={voiceOpen}
          onClose={() => setVoiceOpen(false)}
        />

        <LoginModal
          isOpen={loginOpen}
          onClose={() => setLoginOpen(false)}
          onLogin={(id) => enter(id, true)}
        />
      </div>
    );
  }

  // =========================================================================
  // Loading & State Retrieval
  // =========================================================================
  if (!state) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <Header
          applicantId={applicantId}
          citizenName={activePersona?.name}
          onOpenVoice={() => setVoiceOpen(true)}
          onReset={resetToLanding}
        />
        <NavigationBar
          breadcrumbs={[
            { label: "Citizen Home", onClick: resetToLanding },
            { label: `Citizen: ${applicantId}`, active: true },
          ]}
          onBack={resetToLanding}
          backLabel="← Return to Citizen Homepage"
        />
        <main className="shell narrow" id="main-content">
          {error ? (
            <div className="alert alert-error" role="alert">
              <strong>Error loading application:</strong> {error}
              <div style={{ marginTop: "0.75rem" }}>
                <button type="button" className="btn secondary" onClick={resetToLanding}>
                  ← Back to Citizen Homepage
                </button>
              </div>
            </div>
          ) : (
            <p className="muted" style={{ textAlign: "center", padding: "2rem 0" }}>
              Retrieving verified citizen journey record from National Transport Registry…
            </p>
          )}
        </main>
      </div>
    );
  }

  const stage = state.current_stage;
  const takingTest = stage === "ll_documents_verified" || stage === "ll_test_scheduled";

  // =========================================================================
  // Screen B: Active Journey Shell (Landscape-First Workflow)
  // =========================================================================
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Header
        applicantId={applicantId}
        applicationNumber={state.application_number}
        citizenName={activePersona?.name}
        onOpenVoice={() => setVoiceOpen(true)}
        onReset={resetToLanding}
        onSwitchCitizen={resetToLanding}
      />

      {/* Landscape Horizontal Progression Tracker */}
      <LandscapeJourneyMap
        currentStep={getActiveStepKey(stage, !!review, categoryConfirmed)}
      />

      {/* Universal Breadcrumb & Guaranteed Back Navigation */}
      <NavigationBar
        breadcrumbs={[
          { label: "Citizen Home", onClick: resetToLanding },
          { label: `App #${state.application_number || applicantId}`, onClick: () => setReview(null) },
          { label: review ? "Zero-Form e-KYC Dossier" : state.next_action.label, active: true },
        ]}
        onBack={review ? () => setReview(null) : resetToLanding}
        backLabel={review ? "← Return to Category Selection" : "← Return to Citizen Homepage"}
        stepInfo={getStepInfo(stage)}
      />

      <main className="shell" id="main-content">
        {stageToast && (
          <div className="stage-toast" role="status">
            ✓ Status updated — <strong>{stageToast}</strong>
          </div>
        )}
        {state.stage_detail && (
          <div className="stage-detail-banner">
            <span>ℹ️</span>
            <span>{state.stage_detail}</span>
            {WAITING_STAGES.includes(stage) && (
              <span className="live-sync-note">· live — updates automatically</span>
            )}
          </div>
        )}
        {state.ll_valid_till && (
          <div className="deadline-strip" role="note">
            ⏳ Learner's licence valid till{" "}
            <strong>
              {new Date(state.ll_valid_till).toLocaleDateString("en-IN", {
                day: "numeric",
                month: "long",
                year: "numeric",
              })}
            </strong>{" "}
            — complete your driving test before then. We'll keep this deadline in view.
          </div>
        )}

        {error && error !== "null" && error.trim() !== "" && (
          <p className="alert alert-error" role="alert">{error}</p>
        )}

        {/* ------------------------------------------------------------------
            Step 4 / Review: Verified e-KYC Dossier (Zero-Form Architecture)
            ------------------------------------------------------------------ */}
        {review ? (
          <ReviewConfirm
            view={review}
            submitting={busy}
            onCancel={() => setReview(null)}
            onConfirm={(rto) =>
              act(async () => {
                setState(await journeyApi.apply(applicantId, rto));
                setReview(null);
              })
            }
          />
        ) : (
          <>
            {/* --------------------------------------------------------------
                Stage: no_licence (Step 3: Vehicle Class & Existing Licence)
                -------------------------------------------------------------- */}
            {stage === "no_licence" && (
              <CategorySelector
                selectedCode={selectedCategory}
                existingLicence={verifiedData?.existingLicence}
                onSelect={(code) => setSelectedCategory(code)}
                onProceed={() =>
                  act(async () => {
                    const prof = await journeyApi.verifiedProfile(applicantId);
                    setReview(prof);
                  })
                }
                busy={busy}
              />
            )}

            {/* --------------------------------------------------------------
                Stage: ll_application_submitted (Auto-verifying)
                -------------------------------------------------------------- */}
            {stage === "ll_application_submitted" && (
              <div className="card" style={{ textAlign: "center", padding: "2.5rem" }}>
                <span style={{ fontSize: "2.5rem" }}>⚡</span>
                <h2 style={{ marginTop: "0.5rem" }}>Verifying Digital Documents…</h2>
                <p className="muted">
                  Zero-Form digital records are clearing automated verification via National Transport Registry.
                </p>
                <div style={{ marginTop: "1.5rem" }}>
                  <button
                    type="button"
                    className="btn primary"
                    onClick={() => act(async () => setState(await journeyApi.sync(applicantId)))}
                  >
                    Refresh Status →
                  </button>
                </div>
              </div>
            )}

            {/* --------------------------------------------------------------
                Stage: ll_documents_verified / scheduled (Step 5: LL Test Mode)
                -------------------------------------------------------------- */}
            {takingTest && state.application_number && (
              onlineTestActive ? (
                <LLQuiz
                  applicantId={applicantId}
                  busy={busy}
                  onBack={() => setOnlineTestActive(false)}
                  onResult={(nextState) => setState(nextState)}
                />
              ) : (
                <LLTestSelector
                  onStartOnlineTest={() => setOnlineTestActive(true)}
                  onScheduleCenterTest={async () => {
                    await act(async () => setState(await journeyApi.event(applicantId, "ll_test_scheduled")));
                    setOnlineTestActive(true);
                  }}
                  busy={busy}
                />
              )
            )}

            {/* --------------------------------------------------------------
                Slot Booking Screen (Step 7: Pick Appointment Date & Time)
                -------------------------------------------------------------- */}
            {slots !== null ? (
              <SlotBookingPicker
                slots={slots}
                onConfirmBooking={(slotId, label) =>
                  act(async () => {
                    setBookedSlotLabel(label);
                    setState(await journeyApi.book(applicantId, slotId));
                    setSlots(null);
                  })
                }
                onBack={() => setSlots(null)}
                busy={busy}
              />
            ) : stage === "ll_issued" ? (
              /* --------------------------------------------------------------
                 Stage: ll_issued (Step 6: Digital Learner's Licence Certificate)
                 -------------------------------------------------------------- */
              <LearnerLicenceCard
                applicantId={applicantId}
                applicationNumber={state.application_number ?? undefined}
                citizenName={activePersona?.name}
                vehicleClass={selectedCategory}
                onProceedToPractice={() =>
                  act(async () => {
                    setSlots(await journeyApi.slots(applicantId));
                  })
                }
                busy={busy}
              />
            ) : (stage === "practice_window" || stage === "dl_test_booked" || stage === "dl_test_result_fail") ? (
              /* --------------------------------------------------------------
                 Stage: practice_window / dl_test_booked (Step 8: AI Driving Academy Hub)
                 -------------------------------------------------------------- */
              <PracticeAcademyView
                applicantId={applicantId}
                journeyStage={stage}
                bookedSlotLabel={bookedSlotLabel}
                onProceedToTest={() =>
                  act(async () => setState(await journeyApi.event(applicantId, "attend_dl_test")))
                }
                busy={busy}
              />
            ) : null}

            {/* --------------------------------------------------------------
                Stage: dl_test_result_pass / dl_issued (Step 9: Form 7 DL Card)
                -------------------------------------------------------------- */}
            {(stage === "dl_test_result_pass" || stage === "dl_issued") && (
              <section className="card" aria-label="Issued Licence">
                <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
                  <span className="badge-official">Step 9 of 9 • National Transport Registry</span>
                  <div className="celebrate" style={{ marginTop: "0.4rem" }}>
                    🎉 Permanent Driving Licence Issued!
                  </div>
                  <p className="muted" style={{ fontSize: "0.9rem" }}>
                    All statutory requirements cleared. Your official Form 7 Smart Card is registered in Sarathi.
                  </p>
                </div>

                <div className="licence-wrap">
                  <LicenceCard
                    applicantId={applicantId}
                    applicationNumber={state.application_number ?? "DL-01-2026-998822"}
                    onReturnHome={resetToLanding}
                  />
                </div>

                <div className="card-footer">
                  <button type="button" className="btn secondary" onClick={resetToLanding}>
                    ← Return to Citizen Homepage
                  </button>
                  <button
                    type="button"
                    className="btn primary"
                    onClick={() => alert("Form 7 Smart Card PDF downloaded successfully.")}
                  >
                    📥 Download Form 7 Digital Card
                  </button>
                </div>
              </section>
            )}
          </>
        )}
      </main>

      {/* Bottom Track & Support Strip */}
      <TrackSupportBar
        applicantId={applicantId}
        applicationNumber={state.application_number ?? undefined}
        currentStage={stage}
        onOpenVoice={() => setVoiceOpen(true)}
      />

      <AcademyWidget
        applicantId={applicantId}
        journeyStage={stage}
      />

      <VoiceModal
        applicantId={applicantId}
        journeyStage={stage}
        isOpen={voiceOpen}
        onClose={() => setVoiceOpen(false)}
      />

      <LoginModal
        isOpen={loginOpen}
        onClose={() => setLoginOpen(false)}
        onLogin={(id) => enter(id, true)}
      />

      {state.application_number && (
        <DemoPanel
          state={state}
          onUpdate={(s) => setState(s)}
        />
      )}
    </div>
  );
}
