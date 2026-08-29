// National Driver Training & Safety Academy Embedded Curriculum Panel (Module 4)
// Features Real Video Playback for 8-Turn, Reverse Park, and Hillhold Incline Maneuvers

import { useState } from "react";
import { matchAcademyVideo, type VideoMatchResult } from "../api/client";
import { localVideoMatch } from "../academyFallback";

export interface LessonItem {
  id: string;
  topic: string;
  videoUrl: string;
  icon: string;
  title: string;
  desc: string;
  query: string;
  checkpoints: string[];
}

export const PRACTICAL_LESSONS: LessonItem[] = [
  {
    id: "vid_01_eight_turn",
    topic: "8-turn",
    videoUrl: "/videos/eight_turn.mp4",
    icon: "🔄",
    title: "How to do an 8-Turn (Figure-8 Track)",
    desc: "Master steering wheel hand-over-hand technique and track entry/exit reference points for the RTO 8-track test.",
    query: "How to do an 8 turn",
    checkpoints: [
      "Enter at smooth 15 km/h in 1st/2nd gear",
      "Hand-over-hand steering lock transitions",
      "Maintain 1-foot clearance from track boundary kerbs",
      "Zero vehicle stopping or engine stalling throughout circuit",
    ],
  },
  {
    id: "vid_02_reverse_parking",
    topic: "reverse parking",
    videoUrl: "/videos/reverse_parking.mp4",
    icon: "🅿️",
    title: "How to do Reverse & Bay Parking",
    desc: "Learn mirror alignment, 45-degree angle entry, and smooth reversing without touching track cones or curbs.",
    query: "How to do reverse park",
    checkpoints: [
      "Align rear bumper with outer parking marker cone",
      "Full steering wheel lock at 45° angle",
      "Scan left and right wing mirrors for curb alignment",
      "Complete bay entry in single reverse motion under 3 minutes",
    ],
  },
  {
    id: "vid_03_hill_start",
    topic: "hill start",
    videoUrl: "/videos/hill_start.mp4",
    icon: "⛰️",
    title: "How to do an Incline & Hill-Hold (Stop-Wheel-Hold)",
    desc: "Coordinate handbrake and clutch biting point to take off smoothly uphill on the RTO incline ramp without rollback.",
    query: "How to do an incline stop-wheel-hold",
    checkpoints: [
      "Engage handbrake firmly on 18° incline ramp",
      "Depress clutch and engage 1st gear",
      "Raise clutch to friction biting point until engine note deepens",
      "Smoothly release handbrake while applying throttle (<6 inches rollback)",
    ],
  },
];

export function PracticeAcademyView({
  applicantId,
  journeyStage,
  bookedSlotLabel,
  onProceedToTest,
  busy,
}: {
  applicantId: string;
  journeyStage: string;
  bookedSlotLabel?: string;
  onProceedToTest?: () => void;
  busy?: boolean;
}) {
  const [activeQuery, setActiveQuery] = useState("");
  const [selectedLesson, setSelectedLesson] = useState<LessonItem>(PRACTICAL_LESSONS[0]);
  const [activeMatch, setActiveMatch] = useState<VideoMatchResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleQuery(text: string) {
    if (!text.trim() || loading) return;
    setLoading(true);
    setActiveQuery(text);

    // Look for local matching lesson first
    const lower = text.toLowerCase();
    let matchedLocal: LessonItem | undefined;
    if (lower.includes("8") || lower.includes("eight") || lower.includes("turn") || lower.includes("steer")) {
      matchedLocal = PRACTICAL_LESSONS[0];
    } else if (lower.includes("reverse") || lower.includes("park") || lower.includes("bay") || lower.includes("parallel")) {
      matchedLocal = PRACTICAL_LESSONS[1];
    } else if (lower.includes("hill") || lower.includes("incline") || lower.includes("hold") || lower.includes("slope") || lower.includes("rollback") || lower.includes("high")) {
      matchedLocal = PRACTICAL_LESSONS[2];
    }

    if (matchedLocal) {
      setSelectedLesson(matchedLocal);
    }

    try {
      const res = await matchAcademyVideo(applicantId, text, journeyStage);
      setActiveMatch(res);
    } catch {
      setActiveMatch(localVideoMatch(text));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ marginTop: "0.5rem" }}>
      {/* Appointment Confirmation & Practice Window Header */}
      <div className="alert alert-good" style={{ marginBottom: "1.25rem", borderLeft: "5px solid #16a34a" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "0.5rem" }}>
          <div>
            <strong style={{ fontSize: "1rem" }}>
              ✅ Driving Test Appointment Confirmed &amp; Practice Window Active
            </strong>
            <p style={{ marginTop: "0.35rem", fontSize: "0.88rem" }}>
              Appointment Date &amp; Time: <strong>{bookedSlotLabel || "29 Sep 2026 at 10:00 AM"}</strong> (RTO Mall Road ADTT Track 1)
            </p>
          </div>
          <span className="chip" style={{ background: "#dcfce7", color: "#166534", fontWeight: 700 }}>
            ⏱️ 30-Day Practice Window Open
          </span>
        </div>
      </div>

      <div style={{ background: "white", border: "1px solid var(--line)", borderRadius: "var(--radius-lg)", padding: "1.5rem", boxShadow: "var(--shadow-sm)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1rem" }}>
          <div>
            <span className="badge-official">AI Driving Safety Academy · Practical Test Maneuvers</span>
            <h3 style={{ fontSize: "1.2rem", fontWeight: 800, color: "var(--gov-navy)", margin: "0.25rem 0 0" }}>
              Learn &amp; Master Track Driving Skills
            </h3>
            <p style={{ fontSize: "0.85rem", color: "var(--muted)", margin: "0.2rem 0 0" }}>
              Search for any maneuver you are struggling with or watch the standardized video guides below:
            </p>
          </div>
        </div>

        {/* Video Query Bar */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
          <input
            type="text"
            placeholder="Search for: 'How to do an 8 turn', 'How to do an incline stop-wheel-hold', 'reverse park'..."
            value={activeQuery}
            onChange={(e) => setActiveQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleQuery(activeQuery)}
            style={{ flex: 1, fontSize: "0.9rem" }}
          />
          <button
            type="button"
            className="btn primary"
            onClick={() => handleQuery(activeQuery)}
            disabled={loading || !activeQuery.trim()}
            style={{ whiteSpace: "nowrap", padding: "0.65rem 1.25rem" }}
          >
            {loading ? "Searching…" : "Search Video"}
          </button>
        </div>

        {/* Quick Topic Filter Pills */}
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1.25rem" }}>
          {PRACTICAL_LESSONS.map((l) => {
            const isSelected = selectedLesson.id === l.id;
            return (
              <button
                key={l.id}
                type="button"
                className={`btn ${isSelected ? "primary" : "secondary"}`}
                style={{ fontSize: "0.82rem", padding: "0.4rem 0.85rem", borderRadius: "999px" }}
                onClick={() => {
                  setSelectedLesson(l);
                  setActiveQuery(l.query);
                  handleQuery(l.query);
                }}
              >
                <span>{l.icon}</span> {l.title}
              </button>
            );
          })}
        </div>

        {/* Match Relevance Banner */}
        {activeMatch && (
          <div
            style={{
              background: "var(--gov-blue-subtle)",
              border: "1px solid #bfdbfe",
              borderRadius: "var(--radius-md)",
              padding: "0.85rem 1rem",
              marginBottom: "1.25rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <strong style={{ color: "var(--gov-navy)", fontSize: "0.9rem" }}>
                🎯 Selected Lesson: {selectedLesson.title}
              </strong>
              <div style={{ fontSize: "0.8rem", color: "var(--ink-secondary)" }}>
                {activeMatch.fallback_message || "Video loaded from MoRTH Driving Academy catalog."}
              </div>
            </div>
            <span className="chip" style={{ background: "white", border: "1px solid #93c5fd" }}>
              {Math.round((activeMatch.confidence || 0.95) * 100)}% Match
            </span>
          </div>
        )}

        {/* Video Player & Checklist Showcase */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.25rem", background: "#f8fafc", padding: "1.25rem", borderRadius: "var(--radius-md)", border: "1px solid var(--line)" }}>
          {/* Real Video Player */}
          <div>
            <div style={{ position: "relative", borderRadius: "8px", overflow: "hidden", background: "#000", boxShadow: "var(--shadow-md)" }}>
              <video
                key={selectedLesson.videoUrl}
                controls
                autoPlay
                muted
                style={{ width: "100%", height: "240px", objectFit: "cover", display: "block" }}
                src={selectedLesson.videoUrl}
              >
                Your browser does not support HTML5 video.
              </video>
            </div>
            <div style={{ marginTop: "0.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--gov-navy)" }}>
                🎬 Video File: {selectedLesson.videoUrl.split("/").pop()}
              </span>
              <span style={{ fontSize: "0.75rem", color: "var(--ink-muted)" }}>HD 1080p · Audio Enabled</span>
            </div>
          </div>

          {/* Maneuver Checkpoints & ADTT Track Sensor Standards */}
          <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
            <div>
              <h4 style={{ fontSize: "0.95rem", fontWeight: 800, color: "var(--gov-navy)", margin: "0 0 0.4rem" }}>
                📋 ADTT Evaluation Checklist &amp; Technique:
              </h4>
              <p style={{ fontSize: "0.84rem", color: "var(--ink-secondary)", marginBottom: "0.6rem" }}>
                {selectedLesson.desc}
              </p>
              <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.82rem", color: "#334155", lineHeight: 1.6 }}>
                {selectedLesson.checkpoints.map((cp, idx) => (
                  <li key={idx}><strong>{cp}</strong></li>
                ))}
              </ul>
            </div>

            <div style={{ marginTop: "1rem", padding: "0.6rem", background: "#ecfdf5", border: "1px solid #a7f3d0", borderRadius: "6px", fontSize: "0.8rem", color: "#065f46" }}>
              💡 <strong>Pro Tip:</strong> Use the voice assistant (<code>बोल के अप्लाई</code>) anytime for spoken Hindi/English advice on this maneuver!
            </div>
          </div>
        </div>

        {/* Action to simulate attending the test */}
        {onProceedToTest && (
          <div className="card-footer" style={{ marginTop: "1.75rem" }}>
            <div style={{ fontSize: "0.85rem", color: "var(--ink-muted)" }}>
              After completing your practice window, appear at RTO Track 1 on your scheduled appointment date.
            </div>
            <button
              type="button"
              className="btn primary"
              onClick={onProceedToTest}
              disabled={busy}
              style={{ padding: "0.65rem 1.4rem" }}
            >
              {busy ? "Loading…" : "Simulate Appearing for Driving Test (ADTT) →"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
