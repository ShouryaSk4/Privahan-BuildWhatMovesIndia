// Bol Ke Apply (Module 6) Voice & Conversational Assistant Modal powered by Gemini 2.5 Flash Lite

import { useEffect, useRef, useState } from "react";
import { BOL_URL } from "../api/client";

interface SpeechRecognitionEvent {
  results: {
    [index: number]: {
      [index: number]: {
        transcript: string;
      };
    };
  };
}

interface SpeechRecognitionInstance {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: (() => void) | null;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((error: unknown) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionInstance;
    webkitSpeechRecognition?: new () => SpeechRecognitionInstance;
  }
}

interface Message {
  sender: "user" | "bot";
  text: string;
  toolTag?: string;
}

export function VoiceModal({
  applicantId,
  journeyStage,
  isOpen,
  onClose,
}: {
  applicantId: string;
  journeyStage?: string;
  isOpen: boolean;
  onClose: () => void;
}) {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "bot",
      text: "नमस्ते! मैं 'बोल के अप्लाई' सहायक हूँ। आप बोलकर या लिखकर RTO नियम, ड्राइविंग टेस्ट ट्रैक तकनीक या अपना आवेदन स्टेटस पूछ सकते हैं।",
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [busy, setBusy] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window !== "undefined" && ("SpeechRecognition" in window || "webkitSpeechRecognition" in window)) {
      const SpeechClass = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechClass) {
        const rec = new SpeechClass();
        rec.continuous = false;
        rec.interimResults = false;
        rec.lang = "hi-IN";

        rec.onstart = () => setIsListening(true);
        rec.onend = () => setIsListening(false);
        rec.onerror = () => setIsListening(false);
        rec.onresult = (e: SpeechRecognitionEvent) => {
          const transcript = e.results[0][0].transcript;
          setInputText(transcript);
          handleSend(transcript);
        };
        recognitionRef.current = rec;
      }
    }
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isOpen]);

  const toggleListen = () => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser. You can type your question.");
      return;
    }
    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
  };

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || inputText).trim();
    if (!query || busy) return;

    setMessages((prev) => [...prev, { sender: "user", text: query }]);
    setInputText("");
    setBusy(true);

    const activeId = applicantId || "applicant_001";

    try {
      // Send query directly to Module 6 Bol Ke Apply (/chat endpoint)
      const chatUrl = `${BOL_URL}/chat`;
      const res = await fetch(chatUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: query,
          applicant_id: activeId,
          journey_stage: journeyStage ?? null,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: data.reply || "जानकारी प्राप्त हो गई है।",
          toolTag: data.tool_called ? `Executed MCP Tool: ${data.tool_called}` : undefined,
        },
      ]);
      // Speak the reply when the backend synthesized audio (OpenAI TTS).
      if (data.audio_url && typeof data.audio_url === "string" && data.audio_url.length > 100) {
        try {
          void new Audio(data.audio_url).play().catch(() => {});
        } catch {
          /* autoplay blocked or unsupported — text reply is already shown */
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: `सॉरी, कनेक्ट करने में समस्या हुई: ${err instanceof Error ? err.message : String(err)}। कृपया दोबारा प्रयास करें।`,
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="voice-modal-overlay" onClick={onClose}>
      <div className="voice-modal" onClick={(e) => e.stopPropagation()}>
        <div className="voice-modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <span style={{ fontSize: "1.25rem" }}>🎙️</span>
            <div>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0 }}>बोल के अप्लाई (Bol Ke Apply)</h3>
            </div>
          </div>
          <button
            type="button"
            className="btn ghost"
            style={{ color: "white", padding: "0.2rem 0.6rem" }}
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        <div className="voice-modal-body">
          <div
            ref={scrollRef}
            style={{
              height: "250px",
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "0.65rem",
              padding: "0.85rem",
              background: "#f8fafc",
              borderRadius: "8px",
              border: "1px solid #e2e8f0",
            }}
          >
            {messages.map((m, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: m.sender === "user" ? "flex-end" : "flex-start",
                  background: m.sender === "user" ? "#1e4b9e" : "white",
                  color: m.sender === "user" ? "white" : "#0f172a",
                  padding: "0.65rem 0.9rem",
                  borderRadius: m.sender === "user" ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                  fontSize: "0.88rem",
                  maxWidth: "85%",
                  border: m.sender === "bot" ? "1px solid #e2e8f0" : "none",
                  whiteSpace: "pre-line",
                  boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
                }}
              >
                {m.text}
                {m.toolTag && (
                  <div
                    style={{
                      fontSize: "0.68rem",
                      background: "#e0e7ff",
                      color: "#3730a3",
                      padding: "0.15rem 0.45rem",
                      borderRadius: "4px",
                      marginTop: "0.35rem",
                      display: "inline-block",
                      fontWeight: 700,
                    }}
                  >
                    ⚙️ {m.toolTag}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: "0.4rem", overflowX: "auto", paddingBottom: "0.2rem" }}>
            <button
              type="button"
              className="btn secondary"
              style={{ fontSize: "0.75rem", padding: "0.35rem 0.65rem", borderRadius: "999px", whiteSpace: "nowrap" }}
              onClick={() => handleSend("Mera verified profile dikhao")}
            >
              👤 Mera profile
            </button>
            <button
              type="button"
              className="btn secondary"
              style={{ fontSize: "0.75rem", padding: "0.35rem 0.65rem", borderRadius: "999px", whiteSpace: "nowrap" }}
              onClick={() => handleSend("reverse parking ka sahi tarika batao")}
            >
              🅿️ Reverse parking
            </button>
            <button
              type="button"
              className="btn secondary"
              style={{ fontSize: "0.75rem", padding: "0.35rem 0.65rem", borderRadius: "999px", whiteSpace: "nowrap" }}
              onClick={() => handleSend("8 track pe car kaise modna hai")}
            >
              🔄 8-Track tips
            </button>
            <button
              type="button"
              className="btn secondary"
              style={{ fontSize: "0.75rem", padding: "0.35rem 0.65rem", borderRadius: "999px", whiteSpace: "nowrap" }}
              onClick={() => handleSend("Mera next step kya hai?")}
            >
              📋 What's Next
            </button>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <button
              type="button"
              className={`voice-mic-big ${isListening ? "listening" : ""}`}
              onClick={toggleListen}
              title={isListening ? "Listening... click to stop" : "Click to speak"}
              style={{ margin: 0, width: "46px", height: "46px", fontSize: "1.25rem", flexShrink: 0 }}
            >
              {isListening ? "🔴" : "🎙️"}
            </button>
            <input
              type="text"
              value={inputText}
              placeholder="Speak or type in Hindi, English, Hinglish..."
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              style={{ flex: 1, padding: "0.65rem 0.85rem", fontSize: "0.9rem" }}
            />
            <button
              type="button"
              className="btn primary"
              onClick={() => handleSend()}
              disabled={busy || !inputText.trim()}
              style={{ padding: "0.65rem 1.1rem" }}
            >
              {busy ? "…" : "Send"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
