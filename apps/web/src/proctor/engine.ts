// Integrity engine for the proctored STALL exam.
//
// Design principles (from the project's proctoring guardrails):
//   1. TIERED, NEVER AUTO-FAIL — signals lower a score and set a review tier;
//      a human RTO officer judges flagged sessions. The exam itself is never
//      terminated by the machine.
//   2. EQUITY-AWARE — a denied or missing camera caps the tier at "review",
//      it does not punish the score. Poor lighting must not fail anyone.
//   3. HONEST — every number shown to the citizen comes from a real observed
//      event. Nothing is simulated.
//
// Pure TypeScript: no DOM access, fully unit-tested.

export type SignalType =
  | "tab_hidden"
  | "window_blur"
  | "fullscreen_exit"
  | "face_absent"
  | "multiple_faces"
  | "copy_paste"
  | "context_menu"
  | "camera_denied"
  | "camera_unavailable";

export interface IntegrityEvent {
  t: number; // ms since exam start
  type: SignalType;
  detail: string;
}

export type IntegrityTier = "clear" | "review" | "flagged";

export interface IntegrityReport {
  score: number;
  tier: IntegrityTier;
  events: IntegrityEvent[];
  duration_ms: number;
  camera: "on" | "denied" | "unavailable";
  face_absent_episodes: number;
  multiple_face_episodes: number;
  tab_switches: number;
}

const WEIGHTS: Record<SignalType, number> = {
  tab_hidden: 12,
  window_blur: 4,
  fullscreen_exit: 6,
  face_absent: 8,
  multiple_faces: 15,
  copy_paste: 6,
  context_menu: 2,
  camera_denied: 0, // equity: caps the tier instead of cutting the score
  camera_unavailable: 0,
};

// A signal fired repeatedly within its cooldown counts once — a wobbling
// detector must not shred the score.
const COOLDOWN_MS: Partial<Record<SignalType, number>> = {
  face_absent: 8000,
  multiple_faces: 8000,
  window_blur: 5000,
  context_menu: 3000,
};

export const TIER_THRESHOLDS = { clear: 85, review: 60 } as const;

export class ProctorEngine {
  private startedAt: number;
  private score = 100;
  private events: IntegrityEvent[] = [];
  private lastFired = new Map<SignalType, number>();
  private cameraState: IntegrityReport["camera"] = "on";
  private listeners = new Set<() => void>();

  constructor(private now: () => number = () => Date.now()) {
    this.startedAt = this.now();
  }

  onChange(fn: () => void): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  private emit() {
    this.listeners.forEach((fn) => fn());
  }

  setCameraState(state: IntegrityReport["camera"], detail: string) {
    this.cameraState = state;
    if (state !== "on") {
      this.signal(state === "denied" ? "camera_denied" : "camera_unavailable", detail);
    } else {
      this.emit();
    }
  }

  /** Record a signal. Returns true if it counted (not within cooldown). */
  signal(type: SignalType, detail: string): boolean {
    const t = this.now() - this.startedAt;
    const cooldown = COOLDOWN_MS[type] ?? 0;
    const last = this.lastFired.get(type);
    if (cooldown > 0 && last !== undefined && t - last < cooldown) {
      return false;
    }
    this.lastFired.set(type, t);
    this.events.push({ t, type, detail });
    this.score = Math.max(0, this.score - WEIGHTS[type]);
    this.emit();
    return true;
  }

  count(type: SignalType): number {
    return this.events.filter((e) => e.type === type).length;
  }

  currentScore(): number {
    return this.score;
  }

  currentTier(): IntegrityTier {
    // No camera evidence → an officer must look, however clean the rest was.
    const cap: IntegrityTier = this.cameraState === "on" ? "clear" : "review";
    let tier: IntegrityTier;
    if (this.score >= TIER_THRESHOLDS.clear) tier = "clear";
    else if (this.score >= TIER_THRESHOLDS.review) tier = "review";
    else tier = "flagged";
    if (tier === "clear" && cap === "review") return "review";
    return tier;
  }

  report(): IntegrityReport {
    return {
      score: this.score,
      tier: this.currentTier(),
      events: [...this.events],
      duration_ms: this.now() - this.startedAt,
      camera: this.cameraState,
      face_absent_episodes: this.count("face_absent"),
      multiple_face_episodes: this.count("multiple_faces"),
      tab_switches: this.count("tab_hidden"),
    };
  }
}

export function describeTier(tier: IntegrityTier): string {
  switch (tier) {
    case "clear":
      return "Clear — no review needed";
    case "review":
      return "Officer review — flags are checked by a human, they never auto-fail you";
    case "flagged":
      return "Flagged for officer review — a human will decide, this is not a fail";
  }
}
