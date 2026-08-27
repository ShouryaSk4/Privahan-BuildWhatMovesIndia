// Local development fallback for the Driving Academy widget, used only when
// Module 4's service is unreachable (it is built in a separate silo). The
// topic list mirrors AGENTS.md §5.4 + the §10.6 placeholder suggestions.
// This is a dev convenience, not a reimplementation of Module 4: the real
// service owns matching (LLM classification) and the video library.

import type { VideoMatchResult } from "./api/client";

const TOPICS: { topic: string; videoId: string; keywords: string[] }[] = [
  { topic: "8-turn", videoId: "vid-8-turn", keywords: ["8", "eight", "figure", "circuit"] },
  { topic: "Reverse parking", videoId: "vid-reverse-parking", keywords: ["reverse", "back", "parking"] },
  { topic: "Hill start", videoId: "vid-hill-start", keywords: ["hill", "slope", "incline", "rollback"] },
  { topic: "Clutch control", videoId: "vid-clutch", keywords: ["clutch", "stall", "gear"] },
  { topic: "Steering", videoId: "vid-steering", keywords: ["steering", "steer", "wheel", "turn"] },
  { topic: "Lane change", videoId: "vid-lane-change", keywords: ["lane", "merge", "overtake"] },
  { topic: "Parallel parking", videoId: "vid-parallel-parking", keywords: ["parallel"] },
  { topic: "Emergency braking", videoId: "vid-emergency-braking", keywords: ["brake", "braking", "stop", "emergency"] },
  { topic: "Mirror and signal checks", videoId: "vid-mirrors-signals", keywords: ["mirror", "signal", "indicator", "blind"] },
  { topic: "Gradient descent", videoId: "vid-gradient-descent", keywords: ["descent", "downhill", "engine braking"] },
];

export function localVideoMatch(query: string): VideoMatchResult {
  const words = query.toLowerCase();
  let best: { topic: string; videoId: string; score: number } | null = null;
  for (const t of TOPICS) {
    const score = t.keywords.filter((k) => words.includes(k)).length;
    if (score > 0 && (best === null || score > best.score)) {
      best = { topic: t.topic, videoId: t.videoId, score };
    }
  }
  if (!best) {
    return {
      video_id: "",
      topic: "",
      confidence: 0,
      fallback_message:
        "No lesson matches that yet. Try describing the manoeuvre — for example “I keep rolling back on hill starts”.",
    };
  }
  return {
    video_id: best.videoId,
    topic: best.topic,
    confidence: Math.min(0.55 + best.score * 0.15, 0.9),
    fallback_message: "Academy service offline — matched locally (dev fallback).",
  };
}
