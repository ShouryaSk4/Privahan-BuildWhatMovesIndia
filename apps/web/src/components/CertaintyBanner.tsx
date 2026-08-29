// The informational half of the Certainty Contract, straight from Module 2.
// Formal statutory schedule under Central Motor Vehicles Rules (CMVR).

import type { JourneyState } from "../api/client";

export function CertaintyBanner({ certainty }: { certainty: JourneyState["certainty"] }) {
  return (
    <div className="certainty" role="note" aria-label="What this journey costs">
      <div className="certainty-item">
        <span className="certainty-label-top">Statutory Tariff (Rule 32 CMVR)</span>
        <span className="certainty-value">₹{certainty.cost_inr.toLocaleString("en-IN")}</span>
        <span className="certainty-label">Total official government fee (LL + DL + Smart Card)</span>
      </div>
      <div className="certainty-item">
        <span className="certainty-label-top">Standard Processing Window</span>
        <span className="certainty-value">~{certainty.eta_days} days</span>
        <span className="certainty-label">From application submission to digital licence</span>
      </div>
      <div className="certainty-item">
        <span className="certainty-label-top">Physical Track Requirement</span>
        <span className="certainty-value">{certainty.visit_count} visit</span>
        <span className="certainty-label">Only the automated driving test track requires physical presence</span>
      </div>
    </div>
  );
}
