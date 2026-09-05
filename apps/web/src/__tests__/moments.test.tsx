import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { deriveLicenceNumber } from "../components/LicenceCard";
import { LLQuiz, PASS_MARK, QUESTIONS, scoreQuiz } from "../components/LLQuiz";

describe("scoreQuiz", () => {
  it("counts correct answers", () => {
    expect(scoreQuiz(QUESTIONS.map((q) => q.correct))).toBe(QUESTIONS.length);
    expect(scoreQuiz(QUESTIONS.map(() => null))).toBe(0);
  });

  it("pass mark allows one wrong answer", () => {
    const answers = QUESTIONS.map((q) => q.correct);
    answers[0] = (QUESTIONS[0].correct + 1) % QUESTIONS[0].options.length;
    expect(scoreQuiz(answers)).toBeGreaterThanOrEqual(PASS_MARK);
  });
});

describe("LLQuiz", () => {
  it("reports a pass to the journey after answering correctly", async () => {
    const onResult = vi.fn();
    render(<LLQuiz onResult={onResult} busy={false} />);

    for (const q of QUESTIONS) {
      await userEvent.click(screen.getByRole("radio", { name: q.options[q.correct] }));
    }
    await userEvent.click(screen.getByRole("button", { name: /Submit answers/ }));

    // third arg: the real integrity report (jsdom has no camera → honest "unavailable")
    expect(onResult).toHaveBeenCalledTimes(1);
    const [passed, score, integrity] = onResult.mock.calls[0];
    expect(passed).toBe(true);
    expect(score).toBe(QUESTIONS.length);
    expect(integrity.camera).toBe("unavailable");
    expect(integrity.tier).toBe("review"); // no camera evidence → human review, never a fail
    expect(integrity.score).toBe(100); // equity: no punishment for missing hardware
    expect(screen.getByRole("status")).toHaveTextContent(/passed/);
  });

  it("offers a no-penalty retry on failure", async () => {
    const onResult = vi.fn();
    render(<LLQuiz onResult={onResult} busy={false} />);

    for (const q of QUESTIONS) {
      const wrong = (q.correct + 1) % q.options.length;
      await userEvent.click(screen.getByRole("radio", { name: q.options[wrong] }));
    }
    await userEvent.click(screen.getByRole("button", { name: /Submit answers/ }));

    expect(onResult).not.toHaveBeenCalled();
    expect(screen.getByRole("status")).toHaveTextContent(/No fee, no penalty/);
    await userEvent.click(screen.getByRole("button", { name: /Try again/ }));
    expect(screen.getByRole("button", { name: /Submit answers/ })).toBeDisabled();
  });
});

describe("deriveLicenceNumber", () => {
  it("formats a stable licence number from the application number", () => {
    expect(deriveLicenceNumber("DL20260000001")).toBe("DL07 2600 00001");
    // deterministic: same input, same output
    expect(deriveLicenceNumber("DL20260000001")).toBe(deriveLicenceNumber("DL20260000001"));
  });
});
