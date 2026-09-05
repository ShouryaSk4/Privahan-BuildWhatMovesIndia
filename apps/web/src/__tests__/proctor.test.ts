import { describe, expect, it } from "vitest";
import { describeTier, ProctorEngine } from "../proctor/engine";

function engineAt(times: number[]): { eng: ProctorEngine; tick: () => void } {
  let i = 0;
  const eng = new ProctorEngine(() => times[Math.min(i, times.length - 1)]);
  return { eng, tick: () => void i++ };
}

describe("ProctorEngine", () => {
  it("starts clear at 100", () => {
    const eng = new ProctorEngine(() => 0);
    expect(eng.currentScore()).toBe(100);
    expect(eng.currentTier()).toBe("clear");
  });

  it("weights signals and computes tiers", () => {
    const eng = new ProctorEngine(() => 0);
    eng.signal("tab_hidden", "t1"); // -12 → 88, clear
    expect(eng.currentTier()).toBe("clear");
    eng.signal("multiple_faces", "m1"); // -15 → 73, review
    expect(eng.currentTier()).toBe("review");
    eng.signal("tab_hidden", "t2"); // -12 → 61 (no cooldown on tab)
    eng.signal("copy_paste", "c1"); // -6 → 55, flagged
    expect(eng.currentTier()).toBe("flagged");
    expect(eng.currentScore()).toBe(55);
  });

  it("cooldown dedupes rapid repeats of the same signal", () => {
    const { eng, tick } = engineAt([0, 1000, 2000, 20000]);
    tick(); // t=1000
    expect(eng.signal("face_absent", "gone")).toBe(true);
    tick(); // t=2000 — within the 8s cooldown
    expect(eng.signal("face_absent", "still gone")).toBe(false);
    tick(); // t=20000 — new episode
    expect(eng.signal("face_absent", "gone again")).toBe(true);
    expect(eng.count("face_absent")).toBe(2);
  });

  it("score never goes below zero", () => {
    const eng = new ProctorEngine(() => 0);
    for (let i = 0; i < 30; i++) eng.signal("tab_hidden", `t${i}`);
    expect(eng.currentScore()).toBe(0);
    expect(eng.currentTier()).toBe("flagged");
  });

  it("equity rule: denied camera caps at review without cutting the score", () => {
    const eng = new ProctorEngine(() => 0);
    eng.setCameraState("denied", "citizen declined");
    expect(eng.currentScore()).toBe(100); // no punishment
    expect(eng.currentTier()).toBe("review"); // but a human must look
  });

  it("report is a complete audit trail", () => {
    const { eng, tick } = engineAt([0, 500, 30000, 31000]);
    tick();
    eng.signal("tab_hidden", "switched to another tab");
    tick();
    eng.signal("multiple_faces", "2 faces");
    tick();
    const report = eng.report();
    expect(report.events).toHaveLength(2);
    expect(report.events[0]).toMatchObject({ type: "tab_hidden", t: 500 });
    expect(report.tab_switches).toBe(1);
    expect(report.multiple_face_episodes).toBe(1);
    expect(report.camera).toBe("on");
    expect(report.duration_ms).toBe(31000);
  });

  it("never claims an automatic fail in citizen-facing copy", () => {
    expect(describeTier("review")).toMatch(/never auto-fail/);
    expect(describeTier("flagged")).toMatch(/not a fail/);
  });
});
