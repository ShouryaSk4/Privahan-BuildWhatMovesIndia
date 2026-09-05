import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { deriveLicenceNumber } from "../components/LicenceCard";
import { LLQuiz } from "../components/LLQuiz";

// The exam is now server-authoritative — the client fetches a paper (no answer
// key) and posts answers for grading. We mock that boundary.
vi.mock("../api/client", () => {
  const PAPER = {
    pass_mark: 2,
    total: 2,
    questions: [
      { id: "q1", prompt: "Q1?", options: ["A", "B"], icon: "⚠️" },
      { id: "q2", prompt: "Q2?", options: ["C", "D"], icon: "🚸" },
    ],
  };
  const KEY = [0, 1]; // correct indices, known only to the "server"
  return {
    journeyApi: {
      getExam: vi.fn().mockResolvedValue(PAPER),
      submitExam: vi.fn(async (_id: string, answers: (number | null)[]) => {
        let score = 0;
        const outcomes = PAPER.questions.map((q, i) => {
          const ok = answers[i] === KEY[i];
          if (ok) score += 1;
          return { id: q.id, correct_index: KEY[i], was_correct: ok, explanation: `why ${q.id}` };
        });
        const passed = score >= PAPER.pass_mark;
        return {
          result: { passed, score, total: 2, outcomes, integrity_score: 100, integrity_tier: "review" },
          state: { applicant_id: "applicant_001", current_stage: passed ? "ll_issued" : "ll_documents_verified" },
        };
      }),
    },
  };
});

beforeEach(() => vi.clearAllMocks());

describe("LLQuiz (server-graded)", () => {
  it("passes the returned journey state up when the server says passed", async () => {
    const onResult = vi.fn();
    render(<LLQuiz applicantId="applicant_001" onResult={onResult} busy={false} />);

    // options are rendered from the fetched paper (no answer key in the client)
    await screen.findByRole("radio", { name: "A" });
    await userEvent.click(screen.getByRole("radio", { name: "A" }));
    await userEvent.click(screen.getByRole("radio", { name: "D" }));
    await userEvent.click(screen.getByRole("button", { name: /Submit answers/ }));

    await waitFor(() => expect(onResult).toHaveBeenCalledTimes(1));
    expect(onResult.mock.calls[0][0].current_stage).toBe("ll_issued");
    expect(screen.getByRole("status")).toHaveTextContent(/passed/);
  });

  it("offers a no-penalty retry when the server says failed", async () => {
    const onResult = vi.fn();
    render(<LLQuiz applicantId="applicant_001" onResult={onResult} busy={false} />);

    await screen.findByRole("radio", { name: "B" });
    await userEvent.click(screen.getByRole("radio", { name: "B" })); // wrong
    await userEvent.click(screen.getByRole("radio", { name: "C" })); // wrong
    await userEvent.click(screen.getByRole("button", { name: /Submit answers/ }));

    await screen.findByText(/No fee, no penalty/);
    expect(onResult).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: /Try again/ }));
    expect(screen.getByRole("button", { name: /Submit answers/ })).toBeDisabled();
  });
});

describe("deriveLicenceNumber", () => {
  it("formats a stable licence number from the application number", () => {
    expect(deriveLicenceNumber("DL20260000001")).toBe("DL07 2600 00001");
    expect(deriveLicenceNumber("DL20260000001")).toBe(deriveLicenceNumber("DL20260000001"));
  });
});
