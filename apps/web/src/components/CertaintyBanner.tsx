// The informational half of the Certainty Contract, straight from Module 2.
// Formal statutory schedule under Central Motor Vehicles Rules (CMVR).
// Values count up on arrival — certainty should feel earned, not static.

import { useEffect, useRef, useState } from "react";
import type { JourneyState } from "../api/client";

function useCountUp(target: number, durationMs = 900): number {
  const [value, setValue] = useState(() => {
    // No matchMedia (jsdom/SSR) or reduced motion → show the final value at once.
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return target;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? target : 0;
  });
  const raf = useRef<number>(0);

  useEffect(() => {
    if (value === target) return;
    const start = performance.now();
    const from = 0;
    const tick = (now: number) => {
      const p = Math.min((now - start) / durationMs, 1);
      const eased = 1 - Math.pow(1 - p, 3); // ease-out cubic
      setValue(Math.round(from + (target - from) * eased));
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, durationMs]);

  return value;
}

export function CertaintyBanner({ certainty }: { certainty: JourneyState["certainty"] }) {
  const cost = useCountUp(certainty.cost_inr);
  const days = useCountUp(certainty.eta_days, 750);
  const visits = useCountUp(certainty.visit_count, 600);

  return (
    <div className="certainty" role="note" aria-label="What this journey costs">
      <div className="certainty-item">
        <span className="certainty-label-top">Statutory Tariff (Rule 32 CMVR)</span>
        <span className="certainty-value">₹{cost.toLocaleString("en-IN")}</span>
        <span className="certainty-label">Total official government fee (LL + DL + Smart Card)</span>
      </div>
      <div className="certainty-item">
        <span className="certainty-label-top">Standard Processing Window</span>
        <span className="certainty-value">~{days} days</span>
        <span className="certainty-label">From application submission to digital licence</span>
      </div>
      <div className="certainty-item">
        <span className="certainty-label-top">Physical Track Requirement</span>
        <span className="certainty-value">{visits} visit</span>
        <span className="certainty-label">Only the automated driving test track requires physical presence</span>
      </div>
    </div>
  );
}
