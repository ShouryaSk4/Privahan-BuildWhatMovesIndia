import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { localVideoMatch } from "../academyFallback";
import { CertaintyBanner } from "../components/CertaintyBanner";
import { JourneyRail } from "../components/JourneyRail";
import { ReviewConfirm } from "../components/ReviewConfirm";

describe("CertaintyBanner", () => {
  it("shows the informational Certainty Contract from Module 2", () => {
    render(
      <CertaintyBanner certainty={{ cost_inr: 1350, eta_days: 21, visit_count: 1 }} />,
    );
    expect(screen.getByText("₹1,350")).toBeInTheDocument();
    expect(screen.getByText("~21 days")).toBeInTheDocument();
    expect(screen.getByText("1 visit")).toBeInTheDocument();
  });
});

describe("JourneyRail", () => {
  it("marks the current stage and hides the retry stage unless active", () => {
    render(<JourneyRail currentStage="practice_window" />);
    expect(screen.getByText("Practice").closest("li")).toHaveAttribute("aria-current", "step");
    expect(screen.queryByText("Retry")).not.toBeInTheDocument();
  });

  it("shows the retry stage when the citizen is in it", () => {
    render(<JourneyRail currentStage="dl_test_result_fail" />);
    expect(screen.getByText("Retry").closest("li")).toHaveAttribute("aria-current", "step");
  });
});

const baseProfile = {
  applicant_id: "APL-0002",
  source: "digilocker_aadhaar",
  name: "Asha Sharma",
  dob: "2002-03-14",
  address: "12 Patel Nagar, New Delhi, 110008",
  photo_url: "https://example.invalid/p.jpg",
  gps_suggested_rto: "DL01 (Mall Road)",
  aadhaar_registered_address: "Village Rampur, Sitapur, UP",
  addresses_match: false,
  fetched_at: "2026-08-27T10:00:00Z",
};

const ADDRESS_MISMATCH = {
  field: "aadhaar_registered_address",
  fetched_value: "House 12, Gomti Nagar, Lucknow, UP - 226010",
  issue: "Your current device location suggests a different RTO than your Aadhaar jurisdiction.",
  suggested_fix: "Apply at your Aadhaar jurisdiction RTO, or update your Aadhaar address.",
};

const NAME_MISMATCH = {
  field: "name",
  fetched_value: "Vikram Singh Chauhan",
  issue: "Aadhaar name differs from PAN record 'Vikram S Chauhan'.",
  suggested_fix: "Ensure the full name matches government identity databases.",
};

describe("ReviewConfirm", () => {
  it("surfaces the RTO disagreement and requires an explicit choice", async () => {
    const onConfirm = vi.fn();
    render(
      <ReviewConfirm
        view={{
          profile: baseProfile,
          // Module 3 flags the jurisdiction gap, but Module 2 classifies it as
          // advisory — so the citizen chooses instead of being blocked (§5.3).
          mismatch_check: {
            applicant_id: "applicant_student",
            mismatches: [ADDRESS_MISMATCH],
            clear_to_submit: false,
          },
          blocking_mismatches: [],
          advisory_mismatches: [ADDRESS_MISMATCH],
          clear_to_submit: true,
          gps_rto_choice: "KA-03 Indiranagar",
          aadhaar_rto_choice: "aadhaar_jurisdiction",
        }}
        onConfirm={onConfirm}
        onCancel={() => {}}
        submitting={false}
      />,
    );
    expect(screen.getByText(/Two different RTOs apply to you/)).toBeInTheDocument();

    const submit = screen.getByRole("button", { name: /Confirm & submit/ });
    await userEvent.click(screen.getByRole("checkbox"));
    expect(submit).toBeDisabled(); // still needs the RTO choice

    await userEvent.click(screen.getByRole("radio", { name: /Aadhaar jurisdiction/ }));
    expect(submit).toBeEnabled();
    await userEvent.click(submit);
    expect(onConfirm).toHaveBeenCalledWith("aadhaar_jurisdiction");
  });

  it("blocks submission and shows fixes when identity records mismatch", () => {
    render(
      <ReviewConfirm
        view={{
          profile: { ...baseProfile, addresses_match: true },
          mismatch_check: {
            applicant_id: "applicant_mismatch",
            clear_to_submit: false,
            mismatches: [NAME_MISMATCH],
          },
          blocking_mismatches: [NAME_MISMATCH],
          advisory_mismatches: [],
          clear_to_submit: false,
          gps_rto_choice: "KA-03 Indiranagar",
          aadhaar_rto_choice: null,
        }}
        onConfirm={() => {}}
        onCancel={() => {}}
        submitting={false}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/would be rejected later/);
    expect(screen.queryByRole("button", { name: /Confirm & submit/ })).not.toBeInTheDocument();
  });
});

describe("localVideoMatch (Academy dev fallback)", () => {
  it("matches reverse parking phrasing", () => {
    const result = localVideoMatch("I just can't reverse park the car");
    expect(result.topic).toBe("Reverse parking");
    expect(result.confidence).toBeGreaterThan(0.5);
  });

  it("returns a helpful fallback when nothing matches", () => {
    const result = localVideoMatch("xyzzy");
    expect(result.video_id).toBe("");
    expect(result.fallback_message).toMatch(/describing the manoeuvre/);
  });
});
