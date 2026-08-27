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

describe("ReviewConfirm", () => {
  it("surfaces the RTO disagreement and requires an explicit choice", async () => {
    const onConfirm = vi.fn();
    render(
      <ReviewConfirm
        view={{
          profile: baseProfile,
          mismatch_check: { applicant_id: "APL-0002", mismatches: [], clear_to_submit: true },
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

    await userEvent.click(screen.getByRole("radio", { name: /Aadhaar address/ }));
    expect(submit).toBeEnabled();
    await userEvent.click(submit);
    expect(onConfirm).toHaveBeenCalledWith("UP32");
  });

  it("blocks submission and shows fixes when records mismatch", () => {
    render(
      <ReviewConfirm
        view={{
          profile: { ...baseProfile, addresses_match: true },
          mismatch_check: {
            applicant_id: "APL-0009",
            clear_to_submit: false,
            mismatches: [
              {
                field: "name",
                fetched_value: "Asha Sharma",
                issue: "Aadhaar name does not match school records.",
                suggested_fix: "Attach the name-variation affidavit.",
              },
            ],
          },
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
