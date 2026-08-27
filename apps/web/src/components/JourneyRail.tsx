// The 10-stage journey rail — the citizen always sees where they are.

const STAGES: { key: string; label: string }[] = [
  { key: "no_licence", label: "Start" },
  { key: "ll_application_submitted", label: "Applied" },
  { key: "ll_documents_verified", label: "Verified" },
  { key: "ll_test_scheduled", label: "LL test" },
  { key: "ll_issued", label: "LL issued" },
  { key: "practice_window", label: "Practice" },
  { key: "dl_test_booked", label: "Test booked" },
  { key: "dl_test_result_fail", label: "Retry" },
  { key: "dl_test_result_pass", label: "Passed" },
  { key: "dl_issued", label: "Licence!" },
];

export function JourneyRail({ currentStage }: { currentStage: string }) {
  const currentIdx = STAGES.findIndex((s) => s.key === currentStage);
  // The retry stage only appears on the rail when the citizen is actually in it.
  const visible = STAGES.filter(
    (s) => s.key !== "dl_test_result_fail" || currentStage === "dl_test_result_fail",
  );
  return (
    <ol className="rail" aria-label="Your licence journey">
      {visible.map((s) => {
        const idx = STAGES.findIndex((x) => x.key === s.key);
        const state =
          idx < currentIdx ? "done" : idx === currentIdx ? "current" : "todo";
        return (
          <li key={s.key} className={`rail-step ${state}`} aria-current={state === "current" ? "step" : undefined}>
            <span className="rail-dot" aria-hidden="true" />
            <span className="rail-label">{s.label}</span>
          </li>
        );
      })}
    </ol>
  );
}
