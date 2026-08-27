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
import { CertaintyBanner } from "./components/CertaintyBanner";
import { DemoPanel } from "./components/DemoPanel";
import { JourneyRail } from "./components/JourneyRail";
import { LicenceCard } from "./components/LicenceCard";
import { LLQuiz } from "./components/LLQuiz";
import { ReviewConfirm } from "./components/ReviewConfirm";

// Module 3 keys its e-KYC store on ids like "applicant_001" — case- and
// underscore-sensitive, so the id is passed through exactly as typed.
const APPLICANT_ID_PATTERN = /^[A-Za-z0-9_-]{4,32}$/;

function describeError(e: unknown): string {
  if (e instanceof ApiError) {
    if (typeof e.detail === "string") return e.detail;
    if (e.detail && typeof e.detail === "object" && "message" in e.detail) {
      return String((e.detail as { message: unknown }).message);
    }
  }
  return e instanceof Error ? e.message : String(e);
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

  function enter() {
    const id = idInput.trim();
    if (!APPLICANT_ID_PATTERN.test(id)) {
      setIdError("Use 4–32 letters, digits, dashes or underscores — e.g. applicant_001.");
      return;
    }
    setIdError(null);
    setApplicantId(id);
  }

  if (!applicantId) {
    return (
      <main className="shell narrow">
        <section className="hero" aria-label="Parivahan Seva">
          <p className="hero-eyebrow">Ministry of Road Transport &amp; Highways · MVP</p>
          <h1>Parivahan Seva</h1>
          <p className="hero-tag">Your first driving licence, without the fear.</p>
          <ul className="hero-props">
            <li><b>Zero forms</b> — we fetch, you confirm</li>
            <li><b>₹1,350, ~21 days, 1 visit</b> — promised upfront</li>
            <li><b>A coach in your pocket</b> — for the 30 days in between</li>
          </ul>
        </section>
        <div className="savings" role="note" aria-label="What you save">
          <div className="savings-col agent">
            <span className="savings-label">Agent outside the RTO</span>
            <span className="savings-amount">₹3,500–5,000</span>
            <span className="savings-note">cash, no receipt, no guarantee</span>
          </div>
          <div className="savings-vs" aria-hidden="true">vs</div>
          <div className="savings-col here">
            <span className="savings-label">Doing it here</span>
            <span className="savings-amount">₹1,350</span>
            <span className="savings-note">a receipt for every rupee · you keep ~₹2,650</span>
          </div>
        </div>
        <section className="card" aria-label="Sign in">
          <label htmlFor="applicant">Applicant ID</label>
          <input
            id="applicant"
            value={idInput}
            onChange={(e) => setIdInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && enter()}
          />
          {idError && <p className="alert alert-error">{idError}</p>}
          <p className="muted small">
            Demo personas: <b>applicant_001</b> is a clean journey,{" "}
            <b>applicant_student</b> shows the two-RTO disagreement, and{" "}
            <b>applicant_mismatch</b> shows a blocked application with the fix.
          </p>
          <button className="btn primary" onClick={enter}>Continue</button>
        </section>
      </main>
    );
  }

  if (!state) {
    return (
      <main className="shell narrow">
        {error ? <p className="alert alert-error">{error}</p> : <p>Loading your journey…</p>}
      </main>
    );
  }

  const stage = state.current_stage;
  const takingTest = stage === "ll_documents_verified" || stage === "ll_test_scheduled";

  return (
    <main className="shell">
      <header className="topbar">
        <h1>Parivahan Seva</h1>
        <span className="muted">
          {applicantId}
          {state.application_number && <> · Application {state.application_number}</>}
        </span>
      </header>

      <CertaintyBanner certainty={state.certainty} />
      <JourneyRail currentStage={stage} />
      {state.stage_detail && <p className="stage-detail">{state.stage_detail}</p>}
      {error && <p className="alert alert-error" role="alert">{error}</p>}

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
          <h2>{state.next_action.label}</h2>

          {stage === "no_licence" && (
            <>
              <p className="muted">We already have most of what's needed:</p>
              <ul>
                {state.required_documents.map((d) => (
                  <li key={d.code}>
                    {d.label} {d.satisfied_by_ekyc && <span className="chip">auto via e-KYC</span>}
                  </li>
                ))}
              </ul>
              <button
                className="btn primary"
                disabled={busy}
                onClick={() =>
                  act(async () => setReview(await journeyApi.verifiedProfile(applicantId)))
                }
              >
                {busy ? "Fetching…" : "Fetch my details & start"}
              </button>
            </>
          )}

          {takingTest && state.application_number && (
            <LLQuiz
              busy={busy}
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

          {stage === "ll_issued" && (
            <button
              className="btn primary"
              disabled={busy}
              onClick={() => act(async () => setState(await journeyApi.event(applicantId, "begin_practice")))}
            >
              Start my practice window
            </button>
          )}

          {(stage === "practice_window" || stage === "dl_test_result_fail") && (
            <>
              {slots === null ? (
                <button
                  className="btn primary"
                  disabled={busy}
                  onClick={() => act(async () => setSlots(await journeyApi.slots(applicantId)))}
                >
                  Show driving test slots
                </button>
              ) : (
                <>
                <p className="muted small">Slots at DL01 (Mall Road) — pick any, change anytime before the day:</p>
                <ul className="slots">
                  {slots.slice(0, 6).map((s) => (
                    <li key={s.slot_id}>
                      <span>
                        {new Date(s.starts_at).toLocaleString("en-IN", {
                          weekday: "short",
                          day: "numeric",
                          month: "short",
                          hour: "numeric",
                          minute: "2-digit",
                        })}{" "}
                        · {s.rto_code}
                      </span>
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
                        Book
                      </button>
                    </li>
                  ))}
                </ul>
                </>
              )}
            </>
          )}

          {(stage === "ll_application_submitted" ||
            stage === "dl_test_booked" ||
            stage === "dl_test_result_pass") && (
            <button
              className="btn secondary"
              disabled={busy}
              onClick={() => act(async () => setState(await journeyApi.sync(applicantId)))}
            >
              Check for updates
            </button>
          )}

          {stage === "dl_issued" && state.application_number && (
            <>
              <LicenceCard
                applicantId={applicantId}
                applicationNumber={state.application_number}
              />
              <p className="celebrate">
                🎉 Journey complete — one visit, zero forms, and a coach the whole way.
              </p>
            </>
          )}
        </section>
      )}

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
    </main>
  );
}
