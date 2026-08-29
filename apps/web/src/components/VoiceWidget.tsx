// बोल के अप्लाई — the voice/conversational front door (Module 6).
// Free text and speech both go to the real agent at /chat; nothing is canned
// in the frontend. If the service is down, the widget says so honestly.

import { useRef, useState } from "react";
import { BOL_URL } from "../api/client";

type ChatTurn = {
  who: "user" | "bot";
  text: string;
  tool?: string | null;
};

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  onresult: ((event: { results: { [i: number]: { [j: number]: { transcript: string } } } }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

function getSpeechRecognition(): SpeechRecognitionLike | null {
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
  return Ctor ? new Ctor() : null;
}

export function VoiceWidget({
  applicantId,
  journeyStage,
}: {
  applicantId: string;
  journeyStage: string;
}) {
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [micNote, setMicNote] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  async function send(message: string) {
    const trimmed = message.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setText("");
    setTurns((t) => [...t, { who: "user", text: trimmed }]);
    try {
      const res = await fetch(`${BOL_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          applicant_id: applicantId,
          journey_stage: journeyStage,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const body = (await res.json()) as { reply: string; tool_called?: string | null };
      setTurns((t) => [...t, { who: "bot", text: body.reply, tool: body.tool_called }]);
    } catch {
      setTurns((t) => [
        ...t,
        {
          who: "bot",
          text: "Bol Ke Apply service is offline right now — start services/bol-ke-apply (port 8006) and try again.",
        },
      ]);
    }
    setBusy(false);
    queueMicrotask(() => logRef.current?.scrollTo(0, logRef.current.scrollHeight));
  }

  function listen() {
    const rec = getSpeechRecognition();
    if (!rec) {
      setMicNote("Speech input isn't supported in this browser — type instead.");
      return;
    }
    setMicNote(null);
    rec.lang = "hi-IN";
    rec.interimResults = false;
    rec.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setListening(false);
      void send(transcript);
    };
    rec.onerror = (event) => {
      setListening(false);
      setMicNote(
        event.error === "not-allowed"
          ? "Microphone permission was denied — type instead."
          : `Speech input failed (${event.error}) — type instead.`,
      );
    };
    rec.onend = () => setListening(false);
    setListening(true);
    rec.start();
  }

  if (!open) {
    return (
      <button className="btn voice-fab" onClick={() => setOpen(true)}>
        🎙️ बोल के अप्लाई
      </button>
    );
  }

  return (
    <div className="voice-panel" role="dialog" aria-label="Bol Ke Apply voice assistant">
      <header className="academy-head">
        <span>🎙️ बोल के अप्लाई</span>
        <button className="btn ghost" onClick={() => setOpen(false)} aria-label="Close assistant">
          ✕
        </button>
      </header>
      <div className="academy-log" ref={logRef}>
        {turns.length === 0 && (
          <p className="muted">
            Hindi, English ya Hinglish — kuch bhi poochiye: “mera application status kya
            hai”, “reverse parking kaise karu”, “documents sahi hain kya”.
          </p>
        )}
        {turns.map((turn, i) => (
          <div key={i} className={turn.who === "user" ? "academy-user" : "voice-bot"}>
            <p>{turn.text}</p>
            {turn.tool && <span className="chip">tool: {turn.tool}</span>}
          </div>
        ))}
        {busy && <p className="muted">…</p>}
      </div>
      {micNote && <p className="muted small voice-note">{micNote}</p>}
      <div className="academy-input">
        <button
          className={`btn secondary mic ${listening ? "listening" : ""}`}
          onClick={listen}
          disabled={busy || listening}
          aria-label="Speak"
        >
          {listening ? "👂 Listening…" : "🎙️"}
        </button>
        <input
          value={text}
          placeholder="Boliye ya likhiye…"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(text)}
          aria-label="Message for Bol Ke Apply"
        />
        <button className="btn primary" onClick={() => send(text)} disabled={busy || !text.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
