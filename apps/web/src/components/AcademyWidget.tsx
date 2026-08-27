// Driving Academy chat widget (Module 1 responsibility; matching itself is
// Module 4's job). Falls back to a local matcher when the Academy service —
// built in its own silo — isn't running.

import { useRef, useState } from "react";
import { matchAcademyVideo, type VideoMatchResult } from "../api/client";
import { localVideoMatch } from "../academyFallback";

type ChatEntry =
  | { kind: "user"; text: string }
  | { kind: "match"; result: VideoMatchResult };

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
  const logRef = useRef<HTMLDivElement>(null);

  async function send() {
    const text = query.trim();
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
    queueMicrotask(() => logRef.current?.scrollTo(0, logRef.current.scrollHeight));
  }

  return (
    <div className={`academy ${open ? "open" : ""}`}>
      {open ? (
        <div className="academy-panel" role="dialog" aria-label="Driving Academy">
          <header className="academy-head">
            <span>🛣️ Driving Academy</span>
            <button className="btn ghost" onClick={() => setOpen(false)} aria-label="Close Academy">
              ✕
            </button>
          </header>
          <div className="academy-log" ref={logRef}>
            {entries.length === 0 && (
              <p className="muted">
                Tell me what you're struggling with — “I keep stalling on hill starts”, “reverse
                parking confuses me” — and I'll pull up the right lesson.
              </p>
            )}
            {entries.map((entry, i) =>
              entry.kind === "user" ? (
                <p key={i} className="academy-user">{entry.text}</p>
              ) : entry.result.video_id ? (
                <div key={i} className="academy-match">
                  <div className="academy-video" aria-label={`Lesson video: ${entry.result.topic}`}>
                    ▶ {entry.result.topic}
                  </div>
                  <p className="muted">
                    Matched “{entry.result.topic}” ({Math.round(entry.result.confidence * 100)}%
                    confident).{" "}
                    {entry.result.fallback_message && <em>{entry.result.fallback_message}</em>}
                  </p>
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
            <button className="btn primary" onClick={send} disabled={busy || !query.trim()}>
              {busy ? "…" : "Ask"}
            </button>
          </div>
        </div>
      ) : (
        <button className="btn academy-fab" onClick={() => setOpen(true)}>
          🛣️ Driving Academy
        </button>
      )}
    </div>
  );
}
