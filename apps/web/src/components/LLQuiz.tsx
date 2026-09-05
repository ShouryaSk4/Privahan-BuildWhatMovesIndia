// AI-Proctored Learner's Licence Test (STALL — Screen Test for Aid of Learner's Licence).
//
// Every number on this screen is REAL: face presence comes from an on-device
// MediaPipe detector (no video ever leaves the browser), the integrity score
// comes from observed signals, and flagged sessions go to HUMAN review — the
// machine never fails anyone (see src/proctor/engine.ts for the guardrails).

import { useEffect, useRef, useState } from "react";

import { describeTier, ProctorEngine, type IntegrityReport } from "../proctor/engine";
import { FaceMonitor, type FaceStatus } from "../proctor/faceMonitor";

export type QuizQuestion = {
  id: string;
  prompt: string;
  options: string[];
  correct: number; // index into options
  explanation: string;
  icon?: string;
};

export const QUESTIONS: QuizQuestion[] = [
  {
    id: "triangle",
    prompt: "A red-bordered triangle sign with an exclamation mark means:",
    options: [
      "General caution — slow down and stay alert",
      "Compulsory horn zone",
      "No parking beyond this point",
    ],
    correct: 0,
    explanation: "Triangular signs are cautionary/warning signs indicating potential road hazards ahead.",
    icon: "⚠️",
  },
  {
    id: "zebra",
    prompt: "A pedestrian is waiting at a zebra crossing. You should:",
    options: [
      "Sound the horn and keep moving",
      "Stop and let them cross",
      "Speed up to clear the crossing first",
    ],
    correct: 1,
    explanation: "Pedestrians have legal right of way at marked pedestrian and zebra crossings.",
    icon: "🚶",
  },
  {
    id: "school",
    prompt: "Passing a school zone, the safe speed is:",
    options: ["60 km/h", "40 km/h", "25 km/h"],
    correct: 2,
    explanation: "Standard regulatory speed limit in school and hospital safety zones is 25 km/h.",
    icon: "🏫",
  },
  {
    id: "overtaking",
    prompt: "Overtaking another vehicle is strictly prohibited when approaching:",
    options: [
      "A bend, bridge, or pedestrian crossing",
      "A straight, empty four-lane highway",
      "A wide arterial road with divider",
    ],
    correct: 0,
    explanation: "Under Section 112 MVA, overtaking is forbidden on blind curves, bridges, and pedestrian crossings.",
    icon: "🚫",
  },
  {
    id: "ambulance",
    prompt: "When an emergency ambulance with sirens approaches from behind, you must:",
    options: [
      "Accelerate quickly to stay ahead",
      "Pull safely to the left edge and give clear right of way",
      "Maintain your current lane and speed",
    ],
    correct: 1,
    explanation: "Rule 115 CMVR mandates pulling to the left and granting unobstructed passage to emergency vehicles.",
    icon: "🚑",
  },
];

export const PASS_MARK = 3;

export function scoreQuiz(answers: (number | null)[]): number {
  return QUESTIONS.reduce(
    (score, q, i) => (answers[i] === q.correct ? score + 1 : score),
    0,
  );
}

export function LLQuiz({
  onResult,
  onBack,
  busy,
}: {
  onResult: (passed: boolean, score: number, integrity?: IntegrityReport) => void;
  onBack?: () => void;
  busy: boolean;
}) {
  const [answers, setAnswers] = useState<(number | null)[]>(
    QUESTIONS.map(() => null),
  );
  const [result, setResult] = useState<{ passed: boolean; score: number } | null>(null);
  const allAnswered = answers.every((a) => a !== null);

  // Proctoring state — all of it real
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraNote, setCameraNote] = useState<string | null>(null);
  const [faceStatus, setFaceStatus] = useState<FaceStatus>({ mode: "off", faces: null });
  const [integrity, setIntegrity] = useState({ score: 100, tier: "clear" as const });
  const [violationAlert, setViolationAlert] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const engineRef = useRef<ProctorEngine | null>(null);
  const monitorRef = useRef<FaceMonitor | null>(null);
  const finishedRef = useRef(false);

  function engine(): ProctorEngine {
    if (!engineRef.current) engineRef.current = new ProctorEngine();
    return engineRef.current;
  }

  // Camera + on-device face monitor
  useEffect(() => {
    let active = true;
    const eng = engine();
    const unsubscribe = eng.onChange(() =>
      setIntegrity({ score: eng.currentScore(), tier: eng.currentTier() as "clear" }),
    );

    async function init() {
      if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
        eng.setCameraState("unavailable", "No camera hardware/API in this environment.");
        setCameraNote("No camera available — the session is marked for officer review.");
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 480 }, height: { ideal: 360 } },
          audio: false,
        });
        if (!active) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        setCameraActive(true);
        eng.setCameraState("on", "Camera granted.");

        const monitor = new FaceMonitor();
        monitorRef.current = monitor;
        const mode = await monitor.start(videoRef.current as HTMLVideoElement, (status) => {
          setFaceStatus(status);
          if (status.mode === "full" && status.faces === 0) {
            if (eng.signal("face_absent", "No face visible to the on-device detector.")) {
              setViolationAlert("Face not visible — please stay in front of the camera.");
            }
          }
          if (status.mode === "full" && (status.faces ?? 0) > 1) {
            if (eng.signal("multiple_faces", `${status.faces} faces visible.`)) {
              setViolationAlert("More than one person is visible — the test must be taken alone.");
            }
          }
        });
        if (mode === "basic") {
          setCameraNote("Face analysis model unavailable — camera recorded for officer review only.");
        }
      } catch {
        eng.setCameraState("denied", "Citizen declined camera access.");
        setCameraNote(
          "Camera declined. You can still take the test — the session is marked for officer review (never an automatic fail).",
        );
      }
    }

    init();
    return () => {
      active = false;
      unsubscribe();
      monitorRef.current?.stop();
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Focus / tab / fullscreen / clipboard signals
  useEffect(() => {
    const eng = engine();
    const onVisibility = () => {
      if (document.hidden && !finishedRef.current) {
        eng.signal("tab_hidden", "Test tab hidden (tab switch or window minimised).");
        setViolationAlert(
          `Tab switch recorded (${eng.count("tab_hidden")} so far). Switching away is logged for the reviewing officer.`,
        );
      }
    };
    const onBlur = () => {
      if (!finishedRef.current) eng.signal("window_blur", "Browser window lost focus.");
    };
    const onFsChange = () => {
      if (!document.fullscreenElement && !finishedRef.current) {
        eng.signal("fullscreen_exit", "Left fullscreen during the test.");
      }
    };
    const onCopyPaste = (e: Event) => {
      e.preventDefault();
      eng.signal("copy_paste", `${e.type} attempt blocked.`);
    };
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("blur", onBlur);
    document.addEventListener("fullscreenchange", onFsChange);
    document.addEventListener("copy", onCopyPaste);
    document.addEventListener("paste", onCopyPaste);
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("blur", onBlur);
      document.removeEventListener("fullscreenchange", onFsChange);
      document.removeEventListener("copy", onCopyPaste);
      document.removeEventListener("paste", onCopyPaste);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function submit() {
    const score = scoreQuiz(answers);
    const passed = score >= PASS_MARK;
    finishedRef.current = true;
    monitorRef.current?.stop();
    setResult({ passed, score });
    if (passed) {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      onResult(true, score, engine().report());
    }
  }

  function retry() {
    finishedRef.current = false;
    setAnswers(QUESTIONS.map(() => null));
    setResult(null);
    setViolationAlert(null);
  }

  const faceLabel =
    faceStatus.mode === "full"
      ? faceStatus.faces === 1
        ? "1 face · verified live"
        : faceStatus.faces === 0
          ? "no face visible"
          : `${faceStatus.faces} faces visible`
      : faceStatus.mode === "basic"
        ? "camera on · analysis off"
        : cameraActive
          ? "starting…"
          : "camera off";

  const tierChipStyle =
    integrity.tier === "clear"
      ? { background: "#ecfdf5", color: "#047857" }
      : integrity.tier === "review"
        ? { background: "#fffbeb", color: "#b45309" }
        : { background: "#fef2f2", color: "#b91c1c" };

  return (
    <div
      className="quiz proctored-quiz-shell"
      aria-label="Learner's licence test"
      onContextMenu={(e) => {
        e.preventDefault();
        engine().signal("context_menu", "Right-click blocked.");
      }}
      style={{ userSelect: "none" }}
    >
      {/* Proctoring HUD — every metric here is observed, none simulated */}
      <div className="proctor-hud-bar">
        <div className="proctor-hud-status">
          <span className="hud-indicator pulse" />
          <strong>ON-DEVICE PROCTOR</strong>
          <span className="hud-badge-chrome">🔒 no video leaves this browser</span>
        </div>
        <div className="proctor-hud-metrics">
          <span className={`hud-metric ${faceStatus.mode === "full" && faceStatus.faces !== 1 ? "warning" : ""}`}>
            👤 Face: <strong>{faceLabel}</strong>
          </span>
          <span className="hud-metric">
            🛡️ Integrity: <strong>{integrity.score}/100</strong>
          </span>
          <span className={`hud-metric ${engine().count("tab_hidden") > 0 ? "warning" : ""}`}>
            ⚠️ Tab switches: <strong>{engine().count("tab_hidden")}</strong>
          </span>
        </div>
      </div>

      {violationAlert && (
        <div className="proctor-violation-banner">
          <div>
            <strong>Integrity notice:</strong>
            <p style={{ margin: "0.25rem 0 0", fontSize: "0.85rem" }}>
              {violationAlert} Flags are reviewed by an RTO officer — they never fail you automatically.
            </p>
          </div>
          <button
            type="button"
            className="btn secondary"
            style={{ fontSize: "0.78rem", padding: "0.3rem 0.75rem", background: "white" }}
            onClick={() => setViolationAlert(null)}
          >
            Acknowledge &amp; Resume
          </button>
        </div>
      )}

      <div className="proctor-layout-grid">
        <div className="proctor-questions-column">
          <div className="proctor-exam-banner">
            <div>
              <h2 style={{ fontSize: "1.25rem", fontWeight: 800, margin: "0 0 0.25rem", color: "var(--gov-navy)" }}>
                Screen Test for Aid of Learner's Licence (STALL)
              </h2>
              <p className="muted" style={{ margin: 0, fontSize: "0.88rem" }}>
                Answer all {QUESTIONS.length} multiple choice questions. Passing threshold: <b>{PASS_MARK}/{QUESTIONS.length} (60%)</b>.
              </p>
            </div>
          </div>

          {QUESTIONS.map((q, qi) => (
            <fieldset key={q.id} className="quiz-q proctor-q-card" disabled={result?.passed || busy}>
              <legend style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <span>{q.icon || "📌"}</span>
                <span>Question {qi + 1} of {QUESTIONS.length} — {q.prompt}</span>
              </legend>
              {q.options.map((opt, oi) => (
                <label key={oi} className={result && oi === q.correct ? "quiz-correct" : ""}>
                  <input
                    type="radio"
                    name={q.id}
                    checked={answers[qi] === oi}
                    onChange={() =>
                      setAnswers((a) => a.map((v, i) => (i === qi ? oi : v)))
                    }
                  />
                  <span>{opt}</span>
                </label>
              ))}
              {result && !result.passed && (
                <p style={{ fontSize: "0.82rem", color: "var(--gov-emerald)", marginTop: "0.5rem", fontWeight: 700 }}>
                  💡 Rule Explanation: {q.explanation}
                </p>
              )}
            </fieldset>
          ))}

          <div className="row" style={{ marginTop: "1.25rem" }}>
            {onBack && (
              <button type="button" className="btn secondary" onClick={onBack} disabled={busy}>
                ← Back to Mode Selection
              </button>
            )}

            {result === null ? (
              <button className="btn primary" disabled={!allAnswered || busy} onClick={submit} style={{ padding: "0.65rem 1.4rem" }}>
                {busy ? "Recording result…" : "Submit answers"}
              </button>
            ) : result.passed ? (
              <div className="alert alert-good" role="status" style={{ width: "100%" }}>
                <strong>✅ {result.score}/{QUESTIONS.length} — passed!</strong>{" "}
                Session integrity {engine().currentScore()}/100 · {describeTier(engine().currentTier())}.
                Issuing your official Learner's Licence Form 3…
              </div>
            ) : (
              <div className="alert alert-warn" role="status" style={{ width: "100%" }}>
                <p>
                  <b>Score: {result.score}/{QUESTIONS.length}</b> — The passing threshold is {PASS_MARK}/{QUESTIONS.length}.
                  The correct answers and statutory rules are now highlighted above. No fee, no penalty.
                </p>
                <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem" }}>
                  <button className="btn secondary" onClick={retry}>
                    Try again
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right sidebar: live feed + honest telemetry */}
        <aside className="proctor-feed-column">
          <div className="proctor-webcam-card">
            <div className="webcam-card-header">
              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <span className="live-dot" />
                <span style={{ fontSize: "0.78rem", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                  Live Candidate Feed
                </span>
              </div>
              <span style={{ fontSize: "0.7rem", color: "#93c5fd" }}>on-device analysis</span>
            </div>

            <div className="webcam-viewport">
              <video ref={videoRef} autoPlay playsInline muted className="webcam-video-element" />
              {!cameraActive && (
                <div className="webcam-placeholder">
                  <span>📷 {cameraNote ? "Camera off" : "Initialising camera…"}</span>
                </div>
              )}
              {faceStatus.mode === "full" && (faceStatus.faces ?? 0) >= 1 && (
                <div className="face-bounding-box">
                  <span className="face-box-label">
                    {faceStatus.faces === 1 ? "1 face detected (on-device)" : `${faceStatus.faces} faces detected`}
                  </span>
                </div>
              )}
            </div>

            <div className="webcam-telemetry-body">
              <div className="telemetry-row">
                <span>Face visibility:</span>
                <strong style={{ color: faceStatus.mode === "full" && faceStatus.faces === 1 ? "#166534" : "#b45309" }}>
                  {faceLabel}
                </strong>
              </div>
              <div className="telemetry-row">
                <span>Integrity score:</span>
                <strong>{integrity.score}/100</strong>
              </div>
              <div className="telemetry-row">
                <span>Session status:</span>
                <strong style={{ ...tierChipStyle, padding: "0 0.4rem", borderRadius: "4px" }}>
                  {integrity.tier}
                </strong>
              </div>
              <div className="telemetry-row">
                <span>Signals recorded:</span>
                <strong>{engine().report().events.length}</strong>
              </div>
            </div>

            {cameraNote && (
              <div style={{ fontSize: "0.72rem", color: "#64748b", padding: "0.4rem 0.6rem", background: "#f8fafc", textAlign: "center" }}>
                {cameraNote}
              </div>
            )}
          </div>

          <div className="proctor-rules-card">
            <h4 style={{ fontSize: "0.82rem", fontWeight: 700, margin: "0 0 0.4rem", color: "var(--gov-navy)" }}>
              🔒 How this proctoring works
            </h4>
            <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "0.75rem", color: "var(--ink-secondary)", lineHeight: 1.45 }}>
              <li>Face detection runs on your device — no video or image is ever uploaded.</li>
              <li>Tab switches, focus loss, and copy-paste are recorded as signals.</li>
              <li>Signals lower an integrity score; flagged sessions go to a human RTO officer. Nothing fails you automatically.</li>
            </ul>
          </div>
        </aside>
      </div>
    </div>
  );
}
