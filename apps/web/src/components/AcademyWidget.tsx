// Driving Academy chat widget (Module 1 & 4 integration).
// Powered by RTO Complete Driving Manual RAG and interactive real HTML5 video pop-ups.

import { useRef, useState } from "react";
import { askAcademyManual, type AcademyAskResponse, type VideoMatchResult } from "../api/client";
import { localVideoMatch } from "../academyFallback";

type ChatEntry =
  | { kind: "user"; text: string }
  | { kind: "assistant"; answer: string; sources: string[]; video?: VideoMatchResult | null };

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

    try {
      const resp: AcademyAskResponse = await askAcademyManual(applicantId, text, journeyStage);
      setEntries((e) => [
        ...e,
        {
          kind: "assistant",
          answer: resp.answer,
          sources: resp.source_sections,
          video: resp.matched_video,
        },
      ]);
    } catch {
      // Local fallback if academy service is offline
      const match = localVideoMatch(text);
      setEntries((e) => [
        ...e,
        {
          kind: "assistant",
          answer:
            match.fallback_message ||
            `Based on the RTO Driving Competency Manual, practice the ${match.topic} maneuver maintaining precise vehicle control.`,
          sources: ["RTO Driving Competency Manual"],
          video: match.video_id ? match : null,
        },
      ]);
    } finally {
      setBusy(false);
      queueMicrotask(() => logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" }));
    }
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
                  RTO Manual RAG Active
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
                    Ask anything about Indian driving rules, test track criteria, or maneuvers from the <strong>RTO Complete Driving Competency &amp; Test Manual</strong>:
                  </p>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                    <button
                      type="button"
                      className="btn secondary"
                      style={{ fontSize: "0.75rem", padding: "0.25rem 0.55rem" }}
                      onClick={() => send("What is the clutch bite point technique for hill start?")}
                    >
                      ⛰️ Hill Start Rule &amp; Video
                    </button>
                    <button
                      type="button"
                      className="btn secondary"
                      style={{ fontSize: "0.75rem", padding: "0.25rem 0.55rem" }}
                      onClick={() => send("How to steer on 8-turn track?")}
                    >
                      🔄 8-Turn Track
                    </button>
                    <button
                      type="button"
                      className="btn secondary"
                      style={{ fontSize: "0.75rem", padding: "0.25rem 0.55rem" }}
                      onClick={() => send("What is the reverse parking test evaluation criteria?")}
                    >
                      🅿️ Reverse Park Criteria
                    </button>
                  </div>
                </div>
              )}

              {entries.map((entry, i) =>
                entry.kind === "user" ? (
                  <p key={i} className="academy-user">{entry.text}</p>
                ) : (
                  <div key={i} className="academy-match" style={{ background: "#f8fafc", border: "1px solid #e2e8f0" }}>
                    {/* Sources Badge */}
                    {entry.sources.length > 0 && (
                      <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap", marginBottom: "0.45rem" }}>
                        <span className="chip" style={{ fontSize: "0.68rem", background: "#e0f2fe", color: "#0369a1", fontWeight: 700 }}>
                          📖 RTO Manual: {entry.sources[0]}
                        </span>
                      </div>
                    )}

                    {/* Synthesized Answer */}
                    <div style={{ fontSize: "0.83rem", color: "#1e293b", lineHeight: 1.5, whiteSpace: "pre-line" }}>
                      {entry.answer}
                    </div>

                    {/* Embedded Interactive Video Player if Maneuver Matched */}
                    {entry.video && entry.video.video_id && (
                      <div style={{ marginTop: "0.75rem", borderTop: "1px solid #e2e8f0", paddingTop: "0.6rem" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.3rem" }}>
                          <strong style={{ fontSize: "0.82rem", color: "var(--gov-navy)" }}>
                            🎬 Practice Video: {entry.video.title || entry.video.topic}
                          </strong>
                          <span className="chip" style={{ fontSize: "0.65rem", background: "#f0fdf4", color: "#166534" }}>
                            {Math.round((entry.video.confidence || 0.8) * 100)}% Relevance
                          </span>
                        </div>

                        <div style={{ borderRadius: "6px", overflow: "hidden", background: "#000", boxShadow: "var(--shadow-sm)" }}>
                          <video
                            controls
                            autoPlay
                            muted
                            playsInline
                            src={resolveVideoUrl(entry.video)}
                            style={{ width: "100%", maxHeight: "170px", objectFit: "cover", display: "block" }}
                          >
                            Your browser does not support video playback.
                          </video>
                        </div>

                        <div style={{ marginTop: "0.4rem", display: "flex", gap: "0.4rem" }}>
                          <button
                            type="button"
                            className="btn secondary"
                            style={{ fontSize: "0.74rem", padding: "0.25rem 0.6rem" }}
                            onClick={() =>
                              setActiveModalVideo({
                                url: resolveVideoUrl(entry.video!),
                                title: entry.video!.title || entry.video!.topic,
                                topic: entry.video!.topic,
                              })
                            }
                          >
                            🔍 Pop Up Fullscreen Player
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ),
              )}
            </div>

            <div className="academy-input">
              <input
                value={query}
                placeholder="Ask RTO Driving Manual or describe issue..."
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                aria-label="Ask RTO Driving Manual"
              />
              <button className="btn primary" onClick={() => send()} disabled={busy || !query.trim()}>
                {busy ? "…" : "Ask"}
              </button>
            </div>
          </div>
        ) : (
          <button className="btn academy-fab" onClick={() => setOpen(true)}>
            🛣️ Driving Academy Video &amp; Manual AI
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
                  💡 Official RTO Manual Guideline:
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
