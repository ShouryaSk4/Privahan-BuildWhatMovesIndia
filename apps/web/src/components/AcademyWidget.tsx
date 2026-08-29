// Driving Academy chat widget (Module 1 responsibility; matching itself is
// Module 4's job). Features interactive real HTML5 video pop-ups and playback.

import { useRef, useState } from "react";
import { matchAcademyVideo, type VideoMatchResult } from "../api/client";
import { localVideoMatch } from "../academyFallback";

type ChatEntry =
  | { kind: "user"; text: string }
  | { kind: "match"; result: VideoMatchResult };

function resolveVideoUrl(result: VideoMatchResult): string {
  if (result.video_url && result.video_url.startsWith("/videos/")) {
    return result.video_url;
  }
  const t = (result.topic || "").toLowerCase();
  if (t.includes("8") || t.includes("eight") || t.includes("turn") || t.includes("steer")) {
    return "/videos/eight_turn.mp4";
  }
  if (t.includes("reverse") || t.includes("park") || t.includes("bay") || t.includes("parallel")) {
    return "/videos/reverse_parking.mp4";
  }
  if (t.includes("hill") || t.includes("incline") || t.includes("slope") || t.includes("rollback") || t.includes("hold") || t.includes("high") || t.includes("clutch")) {
    return "/videos/hill_start.mp4";
  }
  return "/videos/eight_turn.mp4";
}

export function AcademyWidget({
  applicantId,
  journeyStage,
  initialQuery,
}: {
  applicantId: string;
  journeyStage: string;
  initialQuery?: string;
}) {
  const [open, setOpen] = useState(Boolean(initialQuery));
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [query, setQuery] = useState(initialQuery ?? "");
  const [busy, setBusy] = useState(false);
  const [activeModalVideo, setActiveModalVideo] = useState<{ url: string; title: string; topic: string } | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  async function send(overrideText?: string) {
    const text = (overrideText || query).trim();
    if (!text || busy) return;
    setBusy(true);
    setEntries((e) => [...e, { kind: "user", text }]);
    setQuery("");
    let result: VideoMatchResult;
    try {
      result = await matchAcademyVideo(applicantId, text, journeyStage);
    } catch {
      result = localVideoMatch(text);
    }
    setEntries((e) => [...e, { kind: "match", result }]);
    setBusy(false);
    queueMicrotask(() => logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" }));
  }

  return (
    <>
      <div className={`academy ${open ? "open" : ""}`}>
        {open ? (
          <div className="academy-panel" role="dialog" aria-label="Driving Academy">
            <header className="academy-head">
              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <span>🛣️ Driving Academy</span>
                <span className="chip" style={{ fontSize: "0.68rem", background: "#22c55e", color: "white", padding: "1px 6px" }}>
                  AI Video Coach
                </span>
              </div>
              <button className="btn ghost" onClick={() => setOpen(false)} aria-label="Close Academy">
                ✕
              </button>
            </header>

            <div className="academy-log" ref={logRef}>
              {entries.length === 0 && (
                <div style={{ padding: "0.25rem 0" }}>
                  <p className="muted" style={{ margin: "0 0 0.75rem", fontSize: "0.85rem" }}>
                    Tell me what maneuver you're struggling with — <em>“I keep stalling on hill starts”</em>, <em>“how to do 8 turn”</em>, <em>“reverse parking”</em> — and I'll pull up the video lesson instantly.
                  </p>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                    <button
                      type="button"
                      className="btn secondary"
                      style={{ fontSize: "0.75rem", padding: "0.25rem 0.55rem" }}
                      onClick={() => send("How to do an 8 turn")}
                    >
                      🔄 8-Turn Track
                    </button>
                    <button
                      type="button"
                      className="btn secondary"
                      style={{ fontSize: "0.75rem", padding: "0.25rem 0.55rem" }}
                      onClick={() => send("How to do reverse parking")}
                    >
                      🅿️ Reverse Park
                    </button>
                    <button
                      type="button"
                      className="btn secondary"
                      style={{ fontSize: "0.75rem", padding: "0.25rem 0.55rem" }}
                      onClick={() => send("How to do a hill start stop-wheel-hold")}
                    >
                      ⛰️ Hill Start
                    </button>
                  </div>
                </div>
              )}

              {entries.map((entry, i) =>
                entry.kind === "user" ? (
                  <p key={i} className="academy-user">{entry.text}</p>
                ) : entry.result.video_id ? (
                  <div key={i} className="academy-match">
                    {/* Embedded Interactive Video Player */}
                    <div style={{ borderRadius: "8px", overflow: "hidden", background: "#000", marginTop: "0.25rem", boxShadow: "var(--shadow-sm)" }}>
                      <video
                        controls
                        autoPlay
                        muted
                        playsInline
                        src={resolveVideoUrl(entry.result)}
                        style={{ width: "100%", maxHeight: "170px", objectFit: "cover", display: "block" }}
                      >
                        Your browser does not support video playback.
                      </video>
                    </div>

                    <div style={{ marginTop: "0.4rem", display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                      <strong style={{ fontSize: "0.85rem", color: "var(--gov-navy)" }}>
                        {entry.result.title || `▶ Lesson: ${entry.result.topic}`}
                      </strong>
                      <span className="chip" style={{ fontSize: "0.68rem", background: "#f0fdf4", color: "#166534" }}>
                        {Math.round(entry.result.confidence * 100)}% Match
                      </span>
                    </div>

                    {entry.result.description && (
                      <p style={{ fontSize: "0.78rem", color: "var(--ink-secondary)", margin: "0.25rem 0 0" }}>
                        {entry.result.description}
                      </p>
                    )}

                    <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.4rem" }}>
                      <button
                        type="button"
                        className="btn secondary"
                        style={{ fontSize: "0.74rem", padding: "0.25rem 0.6rem" }}
                        onClick={() =>
                          setActiveModalVideo({
                            url: resolveVideoUrl(entry.result),
                            title: entry.result.title || entry.result.topic,
                            topic: entry.result.topic,
                          })
                        }
                      >
                        🔍 Pop Up Fullscreen Player
                      </button>
                    </div>
                  </div>
                ) : (
                  <p key={i} className="muted">{entry.result.fallback_message}</p>
                ),
              )}
            </div>

            <div className="academy-input">
              <input
                value={query}
                placeholder="What are you struggling with?"
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                aria-label="Describe what you're struggling with"
              />
              <button className="btn primary" onClick={() => send()} disabled={busy || !query.trim()}>
                {busy ? "…" : "Ask"}
              </button>
            </div>
          </div>
        ) : (
          <button className="btn academy-fab" onClick={() => setOpen(true)}>
            🛣️ Driving Academy Video AI
          </button>
        )}
      </div>

      {/* Pop-up Video Modal */}
      {activeModalVideo && (
        <div
          className="modal-overlay"
          onClick={() => setActiveModalVideo(null)}
          style={{ zIndex: 9999 }}
        >
          <div
            className="modal-card"
            style={{ maxWidth: "680px", width: "95%" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <div>
                <span className="badge-official">AI Driving Academy Video Lesson</span>
                <h3 style={{ margin: "0.25rem 0 0", fontSize: "1.15rem", fontWeight: 800 }}>
                  🎬 {activeModalVideo.title}
                </h3>
              </div>
              <button
                type="button"
                className="btn ghost"
                onClick={() => setActiveModalVideo(null)}
                style={{ fontSize: "1.2rem", padding: "0.2rem 0.5rem" }}
              >
                ✕
              </button>
            </div>

            <div className="modal-body" style={{ padding: "1.25rem" }}>
              <div style={{ borderRadius: "8px", overflow: "hidden", background: "#000", boxShadow: "var(--shadow-md)" }}>
                <video
                  controls
                  autoPlay
                  src={activeModalVideo.url}
                  style={{ width: "100%", maxHeight: "380px", objectFit: "cover", display: "block" }}
                >
                  Your browser does not support HTML5 video.
                </video>
              </div>

              <div style={{ marginTop: "1rem", padding: "0.85rem", background: "#f8fafc", borderRadius: "6px", border: "1px solid var(--line)" }}>
                <strong style={{ fontSize: "0.85rem", color: "var(--gov-navy)" }}>
                  💡 Automated Sensor Track (ADTT) Requirement:
                </strong>
                <p style={{ margin: "0.25rem 0 0", fontSize: "0.8rem", color: "var(--ink-secondary)", lineHeight: 1.45 }}>
                  Practice this maneuver precisely as shown. Overhead AI track sensors evaluate lane discipline, wheel rollback, and obstacle clearance during your physical evaluation.
                </p>
              </div>
            </div>

            <div className="modal-footer" style={{ justifyContent: "flex-end" }}>
              <button
                type="button"
                className="btn primary"
                onClick={() => setActiveModalVideo(null)}
              >
                Close Video Player
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
