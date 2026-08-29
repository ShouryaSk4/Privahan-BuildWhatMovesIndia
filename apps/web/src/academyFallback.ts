// Local development fallback for the Driving Academy widget, used only when
// Module 4's service is unreachable.

import type { VideoMatchResult } from "./api/client";

const TOPICS: {
  topic: string;
  videoId: string;
  videoUrl: string;
  title: string;
  desc: string;
  keywords: string[];
}[] = [
  {
    topic: "8-turn",
    videoId: "vid_01_eight_turn",
    videoUrl: "/videos/eight_turn.mp4",
    title: "Mastering the Figure-8 Driving Track",
    desc: "Master steering wheel hand-over-hand technique and track entry/exit reference points for the RTO 8-track test.",
    keywords: ["8", "eight", "figure", "circuit", "turn", "steer", "aath"],
  },
  {
    topic: "Reverse parking",
    videoId: "vid_02_reverse_parking",
    videoUrl: "/videos/reverse_parking.mp4",
    title: "Flawless Reverse & Bay Parking",
    desc: "Learn mirror alignment, 45-degree angle entry, and smooth reversing without touching track cones or curbs.",
    keywords: ["reverse", "back", "parking", "park", "bay", "cone", "peeche"],
  },
  {
    topic: "Hill start",
    videoId: "vid_03_hill_start",
    videoUrl: "/videos/hill_start.mp4",
    title: "Hill Start & Incline Control without Rollback",
    desc: "Coordinate handbrake and clutch biting point to take off smoothly uphill on the RTO incline ramp without rollback.",
    keywords: ["hill", "slope", "incline", "rollback", "hold", "ramp", "high", "chadhai", "dhalan", "stop-wheel-hold"],
  },
  {
    topic: "Clutch control",
    videoId: "vid_04_clutch_control",
    videoUrl: "/videos/hill_start.mp4",
    title: "Clutch Dynamics & Crawl",
    desc: "Smooth gear shifts, friction zone modulation in heavy stop-and-go urban traffic.",
    keywords: ["clutch", "stall", "gear", "band", "bite"],
  },
  {
    topic: "Steering",
    videoId: "vid_05_steering",
    videoUrl: "/videos/eight_turn.mp4",
    title: "Steering & Hand-Over-Hand",
    desc: "Proper 9-and-3 hand posture, rotational recovery, and lane centering discipline.",
    keywords: ["steering", "steer", "wheel", "turn"],
  },
  {
    topic: "Lane change",
    videoId: "vid_06_lane_change",
    videoUrl: "/videos/eight_turn.mp4",
    title: "Safe Lane Change & Highway Merging",
    desc: "Mirror-Signal-Manoeuvre (MSM) routine and safe blind-spot head checks.",
    keywords: ["lane", "merge", "overtake"],
  },
  {
    topic: "Parallel parking",
    videoId: "vid_07_parallel_parking",
    videoUrl: "/videos/reverse_parking.mp4",
    title: "Curb-Side Parallel Parking",
    desc: "Precision curb-side parallel parking between two vehicles on urban streets.",
    keywords: ["parallel"],
  },
  {
    topic: "Emergency braking",
    videoId: "vid_08_emergency_braking",
    videoUrl: "/videos/eight_turn.mp4",
    title: "Emergency Braking & Hazard Response",
    desc: "Firm cadence and threshold braking avoiding wheel lock-up in sudden hazard situations.",
    keywords: ["brake", "braking", "stop", "emergency"],
  },
  {
    topic: "Mirror and signal checks",
    videoId: "vid_09_mirrors_signals",
    videoUrl: "/videos/reverse_parking.mp4",
    title: "Mirror, Signal & Blind Spot Routine",
    desc: "360-degree situational awareness before turning, changing lanes, or reversing.",
    keywords: ["mirror", "signal", "indicator", "blind"],
  },
  {
    topic: "Gradient descent",
    videoId: "vid_10_gradient_descent",
    videoUrl: "/videos/hill_start.mp4",
    title: "Steep Gradient Descent & Engine Braking",
    desc: "Low-gear selection and engine braking to manage steep downhill slope descent safely.",
    keywords: ["descent", "downhill", "engine braking", "slope"],
  },
];

export function localVideoMatch(query: string): VideoMatchResult {
  const words = query.toLowerCase();
  let best: (typeof TOPICS)[0] & { score: number } | null = null;
  for (const t of TOPICS) {
    const score = t.keywords.filter((k) => words.includes(k)).length;
    if (score > 0 && (best === null || score > best.score)) {
      best = { ...t, score };
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
    confidence: Math.min(0.55 + best.score * 0.15, 0.95),
    fallback_message: undefined,
    video_url: best.videoUrl,
    title: best.title,
    description: best.desc,
  };
}
