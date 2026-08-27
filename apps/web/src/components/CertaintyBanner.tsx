// The informational half of the Certainty Contract, straight from Module 2.

import type { JourneyState } from "../api/client";

export function CertaintyBanner({ certainty }: { certainty: JourneyState["certainty"] }) {
  return (
    <div className="certainty" role="note" aria-label="What this journey costs">
      <div className="certainty-item">
        <span className="certainty-value">₹{certainty.cost_inr.toLocaleString("en-IN")}</span>
        <span className="certainty-label">total cost — nothing extra, ever</span>
      </div>
      <div className="certainty-item">
        <span className="certainty-value">~{certainty.eta_days} days</span>
        <span className="certainty-label">start to licence in hand</span>
      </div>
      <div className="certainty-item">
        <span className="certainty-value">{certainty.visit_count} visit</span>
        <span className="certainty-label">only your driving test needs you in person</span>
      </div>
    </div>
  );
}
