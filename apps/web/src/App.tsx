import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  demoRtoApi,
  journeyApi,
  type JourneyState,
  type TestSlot,
  type VerifiedIdentityView,
} from "./api/client";
import { AcademyWidget } from "./components/AcademyWidget";
import { DemoPanel } from "./components/DemoPanel";
import { Header } from "./components/Header";
import { LicenceCard } from "./components/LicenceCard";
import { LLQuiz } from "./components/LLQuiz";
import { NavigationBar } from "./components/NavigationBar";
import { PracticeAcademyView } from "./components/PracticeAcademyView";
import { ReviewConfirm } from "./components/ReviewConfirm";
import { VoiceModal } from "./components/VoiceModal";
import { LoginModal } from "./components/LoginModal";

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
      return "Step 1 of 6: e-KYC Identity Verification";
    case "ll_application_submitted":
      return "Step 2 of 6: Application In Review";
    case "ll_documents_verified":
    case "ll_test_scheduled":
      return "Step 3 of 6: Online Learner's Test (STALL)";
    case "ll_issued":
      return "Step 4 of 6: Learner's Licence Issued";
    case "practice_window":
      return "Step 5 of 6: 30-Day Practice & Road Safety Academy";
    case "dl_test_booked":
      return "Step 5 of 6: Track Test Scheduled (ADTT)";
    case "dl_test_result_fail":
      return "Step 5 of 6: Skill Remediation & Retest";
    case "dl_test_result_pass":
    case "dl_issued":
      return "Step 6 of 6: Permanent Driving Licence Issued";
    default:
      return "Citizen Application Journey";
  }
}

export default function App() {
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

  const refresh = useCallback(async (id: string) => {
    setState(await journeyApi.get(id));
  }, []);

  useEffect(() => {
    if (applicantId) {
      refresh(applicantId).catch((e) => setError(describeError(e)));
    }
  }, [applicantId, refresh]);

  async function act(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (e) {
      setError(describeError(e));
    } finally {
      setBusy(false);
    }
  }

  async function enter(customId?: string, resetFirst = true) {
    const id = (customId || idInput).trim();
    if (!APPLICANT_ID_PATTERN.test(id)) {
      setIdError("Please enter a valid reference ID (4–32 letters, numbers, or dashes) — e.g. applicant_001");
      return;
    }
    setIdError(null);
    setBusy(true);
    try {
      if (resetFirst) {
        await journeyApi.reset(id).catch(() => null);
      }
      const fresh = await journeyApi.get(id);
      setState(fresh);
      setApplicantId(id);
      setReview(null);
      setSlots(null);
    } catch (e) {
      setError(describeError(e));
    } finally {
      setBusy(false);
    }
  }

  function resetToLanding() {
    setApplicantId("");
    setState(null);
    setReview(null);
    setSlots(null);
    setError(null);
  }

  const activePersona = DEMO_PERSONAS.find((p) => p.id === applicantId);

  // =========================================================================
  // Screen A: Task-First Citizen Homepage (Before Sign-In)
  // =========================================================================
  if (!applicantId) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <Header onOpenVoice={() => setVoiceOpen(true)} onOpenLogin={() => setLoginOpen(true)} />

        <main className="shell">
          {/* Hero Section */}
          <section className="task-first-hero" aria-label="Parivahan Seva Overview">
            <p className="hero-eyebrow">Ministry of Road Transport &amp; Highways · Government of India</p>
            <h1>What would you like to do today?</h1>
            <p className="sub">
              Access official transport and licensing services with zero paperwork, transparent statutory fees under Rule 32 CMVR,
              and instant verification through DigiLocker &amp; Aadhaar e-KYC.
            </p>

            {/* Task-First Service Cards */}
            <div className="task-cards-grid">
              <div
                className="task-card featured"
                onClick={() => {
                  setIdInput("applicant_001");
                  enter("applicant_001", true);
                }}
              >
                <div>
                  <div className="task-card-badge">✨ Most Popular</div>
                  <div className="task-card-icon">🚗</div>
                  <div className="task-card-title">Apply for New Driving Licence (LMV)</div>
                  <div className="task-card-desc">
                    Zero-form e-KYC application for first-time car licence. Starts fresh with online learner's test, 30-day safety academy &amp; automated track booking.
                  </div>
                </div>
                <div className="task-card-action">Start Zero-Form Application →</div>
              </div>

              <div
                className="task-card"
                onClick={() => {
                  setIdInput("applicant_student");
                  enter("applicant_student", true);
                }}
              >
                <div>
                  <div className="task-card-icon">📍</div>
                  <div className="task-card-title">Inter-State Mover / Student Application</div>
                  <div className="task-card-desc">
                    Living away from your home state? Choose seamlessly between your legal Aadhaar jurisdiction and local convenience RTO.
                  </div>
                </div>
                <div className="task-card-action">Apply with Location Choice →</div>
              </div>

              <div
                className="task-card"
                onClick={() => {
                  setIdInput("applicant_mismatch");
                  enter("applicant_mismatch", true);
                }}
              >
                <div>
                  <div className="task-card-icon">🛡️</div>
                  <div className="task-card-title">Check Rejection Risk (Pre-Screen)</div>
                  <div className="task-card-desc">
                    Run automated cross-checks against PAN &amp; Aadhaar databases before submission to prevent RTO document rejections.
                  </div>
                </div>
                <div className="task-card-action">Pre-Screen My Records →</div>
              </div>

              <div
                className="task-card"
                onClick={() => setVoiceOpen(true)}
              >
                <div>
                  <div className="task-card-icon">🎙️</div>
                  <div className="task-card-title">बोल के अप्लाई (Voice Assistant)</div>
                  <div className="task-card-desc">
                    Powered by Gemini AI. Speak in Hindi, English, or Hinglish to check status, verify identity, or ask RTO rule questions.
                  </div>
                </div>
                <div className="task-card-action">Open Voice Assistant →</div>
              </div>
            </div>
          </section>

          {/* Quick Sign-In / Demo Persona Selector */}
          <section className="card-signin" aria-label="Sign in to application">
            <h2>Select Citizen Profile or Enter Reference ID</h2>
            <p className="muted" style={{ fontSize: "0.9rem" }}>
              Choose a verified persona below to experience the complete citizen journey end-to-end:
            </p>

            <div className="persona-preset-selector">
              <div className="persona-preset-title">Verified Demo Citizen Profiles:</div>
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
                    <span style={{ fontSize: "0.85rem", color: "var(--gov-blue)", fontWeight: 800 }}>Start Fresh →</span>
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginTop: "1.25rem" }}>
              <label htmlFor="applicant" style={{ fontSize: "0.88rem", fontWeight: 700, color: "var(--gov-navy)" }}>
                Or enter custom Citizen Reference ID:
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
                  Continue Application →
                </button>
              </div>
              <p className="muted small" style={{ marginTop: "0.4rem" }}>
                Format hint: 4–32 letters, numbers, or underscores (e.g. <code>applicant_001</code>)
              </p>
            </div>
            {idError && <p className="alert alert-error">{idError}</p>}
          </section>
        </main>

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
      <div>
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
        <main className="shell narrow">
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
  // Screen B: Active Journey Shell (Guaranteed Back Button on Every View)
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

      {/* Universal Breadcrumb & Guaranteed Back Navigation */}
      <NavigationBar
        breadcrumbs={[
          { label: "Citizen Home", onClick: resetToLanding },
          { label: `App #${state.application_number || applicantId}`, onClick: () => setReview(null) },
          { label: review ? "e-KYC Review" : state.next_action.label, active: true },
        ]}
        onBack={review ? () => setReview(null) : resetToLanding}
        backLabel={review ? "← Return to Application Overview" : "← Return to Citizen Homepage"}
        stepInfo={getStepInfo(stage)}
      />

      <main className="shell">
        {state.stage_detail && (
          <div className="stage-detail-banner">
            <span>ℹ️</span>
            <span>{state.stage_detail}</span>
          </div>
        )}

        {error && <p className="alert alert-error" role="alert">{error}</p>}

        {/* ------------------------------------------------------------------
            Step 1 / Review: Verified e-KYC Dossier
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
          <section className="card" aria-label="Next step">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "0.5rem" }}>
              <h2>{state.next_action.label}</h2>
              <span className="chip">{getStepInfo(stage)}</span>
            </div>

            {/* --------------------------------------------------------------
                Stage: no_licence (Start Zero-Form Application)
                -------------------------------------------------------------- */}
            {stage === "no_licence" && (
              <>
                <p className="muted" style={{ fontSize: "0.92rem", marginTop: "0.5rem" }}>
                  Under the Motor Vehicles Act, your eligibility requirements are automatically verified via National Repositories:
                </p>
                <ul style={{ margin: "0.85rem 0 1.5rem 1.25rem", fontSize: "0.92rem", color: "var(--ink-secondary)" }}>
                  {state.required_documents.map((d) => (
                    <li key={d.code} style={{ margin: "0.35rem 0" }}>
                      <b>{d.label}</b> {d.satisfied_by_ekyc && <span className="chip">Verified via DigiLocker e-KYC</span>}
                    </li>
                  ))}
                </ul>

                <div className="row">
                  <button
                    type="button"
                    className="btn secondary"
                    onClick={resetToLanding}
                    disabled={busy}
                  >
                    ← Back to Citizen Homepage
                  </button>
                  <button
                    className="btn primary"
                    disabled={busy}
                    onClick={() =>
                      act(async () => setReview(await journeyApi.verifiedProfile(applicantId)))
                    }
                  >
                    {busy ? "Authenticating with DigiLocker…" : "Authenticate & Review Verified Profile →"}
                  </button>
                </div>
              </>
            )}

            {/* --------------------------------------------------------------
                Stage: ll_documents_verified / scheduled (Online Learner Test)
                -------------------------------------------------------------- */}
            {takingTest && state.application_number && (
              <LLQuiz
                busy={busy}
                onBack={resetToLanding}
                onResult={(passed) =>
                  act(async () => {
                    if (passed && state.application_number) {
                      await demoRtoApi.reportTestResult(state.application_number, "ll", true);
                      setState(await journeyApi.sync(applicantId));
                    }
                  })
                }
              />
            )}

            {/* --------------------------------------------------------------
                Stage: ll_issued (Learner Licence Ready -> Start Practice)
                -------------------------------------------------------------- */}
            {stage === "ll_issued" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem", marginTop: "0.75rem" }}>
                <div className="alert alert-good">
                  <strong>✅ Official Learner's Licence Form 3 Issued Digitally</strong>
                  <p style={{ marginTop: "0.35rem", fontSize: "0.9rem" }}>
                    Your Learner's Licence has been recorded in the National Sarathi Registry. Pursuant to Rule 15 of CMVR,
                    a 30-day skill acquisition practice window is now active.
                  </p>
                </div>

                <div className="row">
                  <button type="button" className="btn secondary" onClick={resetToLanding} disabled={busy}>
                    ← Back to Citizen Dashboard
                  </button>
                  <button
                    className="btn primary"
                    disabled={busy}
                    onClick={() => act(async () => setState(await journeyApi.event(applicantId, "begin_practice")))}
                  >
                    Enter 30-Day Practice Window &amp; Access Driving Academy →
                  </button>
                </div>
              </div>
            )}

            {/* --------------------------------------------------------------
                Stage: practice_window / dl_test_result_fail (Practice & Academy)
                -------------------------------------------------------------- */}
            {(stage === "practice_window" || stage === "dl_test_result_fail") && (
              <>
                {stage === "dl_test_result_fail" && (
                  <div className="alert alert-warn" style={{ marginBottom: "1.25rem" }}>
                    <strong>Automated Test Track Evaluation Notice:</strong>
                    <p style={{ marginTop: "0.35rem", fontSize: "0.9rem" }}>
                      The test track sensors detected an infraction during your evaluation. You can review the targeted maneuver lessons
                      below and schedule your re-test at zero penalty.
                    </p>
                  </div>
                )}

                {/* Embedded Road Safety Academy Panel */}
                <PracticeAcademyView
                  applicantId={applicantId}
                  journeyStage={stage}
                  busy={busy}
                  onBookSlot={() => act(async () => setSlots(await journeyApi.slots(applicantId)))}
                />

                {/* Slot Booking Grid */}
                {slots !== null && (
                  <div style={{ marginTop: "1.75rem", paddingTop: "1.25rem", borderTop: "1px solid var(--line)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem", flexWrap: "wrap", gap: "0.5rem" }}>
                      <h3 style={{ fontSize: "1.1rem", fontWeight: 800, color: "var(--gov-navy)", margin: 0 }}>
                        Select Automated Test Track Appointment (ADTT)
                      </h3>
                      <button
                        type="button"
                        className="btn ghost"
                        style={{ fontSize: "0.8rem" }}
                        onClick={() => setSlots(null)}
                      >
                        Hide Slots ✕
                      </button>
                    </div>

                    <p className="muted small">
                      Available evaluation appointments at RTO Mall Road Track (DL01) — Pick any slot:
                    </p>

                    <ul className="slots">
                      {slots.slice(0, 6).map((s) => (
                        <li key={s.slot_id}>
                          <div>
                            <div style={{ fontWeight: 700, color: "var(--gov-navy)" }}>
                              {new Date(s.starts_at).toLocaleString("en-IN", {
                                weekday: "short",
                                day: "numeric",
                                month: "short",
                                hour: "numeric",
                                minute: "2-digit",
                              })}
                            </div>
                            <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>
                              Track: {s.rto_code} • {s.capacity_left} slots open
                            </div>
                          </div>
                          <button
                            className="btn secondary"
                            disabled={busy}
                            onClick={() =>
                              act(async () => {
                                setState(await journeyApi.book(applicantId, s.slot_id));
                                setSlots(null);
                              })
                            }
                          >
                            Book Slot
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}

            {/* --------------------------------------------------------------
                Stage: Submitted / Booked / Passed (Awaiting Workflow Action)
                -------------------------------------------------------------- */}
            {(stage === "ll_application_submitted" ||
              stage === "dl_test_booked" ||
              stage === "dl_test_result_pass") && (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "0.75rem" }}>
                <p className="muted" style={{ fontSize: "0.92rem" }}>
                  Application is active in the National Transport Registry. Awaiting official workflow synchronization.
                </p>

                <div className="row">
                  <button type="button" className="btn secondary" onClick={resetToLanding} disabled={busy}>
                    ← Back to Citizen Homepage
                  </button>
                  <button
                    className="btn primary"
                    disabled={busy}
                    onClick={() => act(async () => setState(await journeyApi.sync(applicantId)))}
                  >
                    🔄 Check for Registry Status Updates
                  </button>
                </div>
              </div>
            )}

            {/* --------------------------------------------------------------
                Stage: dl_issued (Permanent Driving Licence Card)
                -------------------------------------------------------------- */}
            {stage === "dl_issued" && state.application_number && (
              <>
                <LicenceCard
                  applicantId={applicantId}
                  applicationNumber={state.application_number}
                  onReturnHome={resetToLanding}
                />
                <p className="celebrate">
                  🎉 Permanent Driving Licence (Form 7) Issued Digitally via Parivahan Seva
                </p>
              </>
            )}
          </section>
        )}

        {/* Floating Academy Assistant & Dev Simulator */}
        <DemoPanel state={state} onUpdate={setState} />
        <AcademyWidget
          key={stage === "dl_test_result_fail" ? "coach" : "idle"}
          applicantId={applicantId}
          journeyStage={stage}
          initialQuery={
            stage === "dl_test_result_fail" && state.stage_detail?.includes("checkpoint")
              ? `I failed at ${state.stage_detail.split("Missed checkpoint: ")[1]?.split(".")[0]?.replaceAll("_", " ") ?? "the test"}`
              : undefined
          }
        />

        {/* Bol Ke Apply Voice Modal */}
        <VoiceModal
          applicantId={applicantId}
          journeyStage={stage}
          isOpen={voiceOpen}
          onClose={() => setVoiceOpen(false)}
        />
      </main>
    </div>
  );
}
