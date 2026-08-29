// National Driver Training & Safety Academy Embedded Curriculum Panel (Module 4)

import { useState } from "react";
import { matchAcademyVideo, type VideoMatchResult } from "../api/client";
import { localVideoMatch } from "../academyFallback";

const ESSENTIAL_LESSONS = [
  {
    id: "vid_01_eight_turn",
    topic: "8-Turn Maneuver",
    icon: "🔄",
    desc: "Mastering steering lock-to-lock transitions and trajectory control on the automated test track.",
    query: "how to steer on 8-track maneuver",
  },
  {
    id: "vid_02_reverse_parking",
    topic: "Reverse & Parallel Parking",
    icon: "🅿️",
    desc: "Mirror alignment, blind-spot checks, and 45-degree angle reverse bay parking technique.",
    query: "reverse parking ka sahi tarika batao",
  },
  {
    id: "vid_03_hill_start",
    topic: "Incline & Hill Start",
    icon: "⛰️",
    desc: "Handbrake-to-clutch bite point balance without engine stall or backward rollback.",
    query: "hill start clutch bite point balance",
  },
  {
    id: "vid_04_clutch_control",
    topic: "Clutch Dynamics & Crawl",
    icon: "⚙️",
    desc: "Smooth gear shifts, friction zone modulation in heavy stop-and-go urban traffic.",
    query: "clutch kaise chhodna hai car band ho jati hai",
  },
  {
    id: "vid_05_steering",
    topic: "Steering & Hand-Over-Hand",
    icon: "🚗",
    desc: "Proper 9-and-3 hand posture, rotational recovery, and lane centering discipline.",
    query: "proper steering technique and control",
  },
];

export function PracticeAcademyView({
  applicantId,
  journeyStage,
  onBookSlot,
  busy,
}: {
  applicantId: string;
  journeyStage: string;
  onBookSlot?: () => void;
  busy?: boolean;
}) {
  const [activeQuery, setActiveQuery] = useState("");
  const [activeMatch, setActiveMatch] = useState<VideoMatchResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleQuery(text: string) {
    if (!text.trim() || loading) return;
    setLoading(true);
    setActiveQuery(text);
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
    <div style={{ marginTop: "1rem" }}>
      <div className="alert alert-good" style={{ marginBottom: "1.25rem" }}>
        <strong>🛡️ 30-Day Mandatory Skill Practice Window Active (Rule 15 CMVR)</strong>
        <p style={{ marginTop: "0.25rem", fontSize: "0.88rem" }}>
          You hold a valid Learner's Licence. Under Central Motor Vehicles Rules, practice driving under the supervision of a licensed driver
          and master the automated track curriculum below before your final physical test.
        </p>
      </div>

      <div style={{ background: "var(--surface)", border: "1px solid var(--line)", borderRadius: "var(--radius-lg)", padding: "1.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1rem" }}>
          <div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 800, color: "var(--gov-navy)", margin: 0 }}>
              🛣️ National Driver Training &amp; Safety Academy
            </h3>
            <p style={{ fontSize: "0.85rem", color: "var(--muted)", margin: "0.2rem 0 0" }}>
              Standardized training curriculum for automated sensor test tracks (ADTT). Click any topic or ask a question:
            </p>
          </div>
        </div>

        {/* Video Query Bar */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.25rem" }}>
          <input
            type="text"
            placeholder="Describe what you want to learn (e.g. 'clutch balance on incline', '8 track steering')..."
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
            style={{ whiteSpace: "nowrap" }}
          >
            {loading ? "Matching…" : "Search Video Lesson"}
          </button>
        </div>

        {/* Match Result Display */}
        {activeMatch && (
          <div
            style={{
              background: "var(--gov-blue-subtle)",
              border: "1px solid #bfdbfe",
              borderRadius: "var(--radius-md)",
              padding: "1rem",
              marginBottom: "1.25rem",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.4rem" }}>
              <div style={{ fontWeight: 800, color: "var(--gov-navy)", fontSize: "0.95rem" }}>
                ▶ Recommended Module: {activeMatch.topic}
              </div>
              <span className="chip" style={{ background: "white", border: "1px solid #93c5fd" }}>
                {Math.round(activeMatch.confidence * 100)}% Match Relevance
              </span>
            </div>
            <p style={{ fontSize: "0.85rem", color: "var(--ink-secondary)", margin: 0 }}>
              {activeMatch.fallback_message || "Video lesson loaded from MoRTH Road Safety Catalog."}
            </p>
          </div>
        )}

        {/* Essential Curriculum Grid */}
        <div className="academy-curriculum-grid">
          {ESSENTIAL_LESSONS.map((l) => (
            <div
              key={l.id}
              className="academy-lesson-card"
              onClick={() => handleQuery(l.query)}
              style={{ cursor: "pointer" }}
            >
              <div>
                <div className="academy-lesson-title">
                  <span>{l.icon}</span>
                  <span>{l.topic}</span>
                </div>
                <p className="academy-lesson-desc">{l.desc}</p>
              </div>
              <button
                type="button"
                className="btn secondary"
                style={{ fontSize: "0.78rem", padding: "0.35rem 0.65rem", alignSelf: "flex-start", minHeight: "32px" }}
              >
                Watch Video Lesson →
              </button>
            </div>
          ))}
        </div>

        {/* Action to proceed to slot booking */}
        {onBookSlot && (
          <div style={{ marginTop: "1.75rem", paddingTop: "1.25rem", borderTop: "1px solid var(--line)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
            <div>
              <div style={{ fontWeight: 700, color: "var(--gov-navy)", fontSize: "0.95rem" }}>
                Ready for your Automated Driving Test Track (ADTT) Evaluation?
              </div>
              <p style={{ fontSize: "0.82rem", color: "var(--muted)", margin: "0.15rem 0 0" }}>
                Choose your preferred appointment date and time at your designated RTO track.
              </p>
            </div>
            <button
              type="button"
              className="btn primary"
              onClick={onBookSlot}
              disabled={busy}
              style={{ padding: "0.75rem 1.5rem" }}
            >
              Schedule Track Test Appointment (ADTT) →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
