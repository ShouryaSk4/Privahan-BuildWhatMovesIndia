// Landscape Journey Progression Map inspired by MoRTH User Journey Architecture

export type JourneyStepKey =
  | "intent"
  | "login"
  | "category"
  | "application"
  | "ll_test"
  | "ll_issued"
  | "practice"
  | "dl_booking"
  | "dl_test";

const STEPS: { key: JourneyStepKey; num: number; title: string; subtitle: string; icon: string }[] = [
  { key: "intent", num: 1, title: "Discover & Intent", subtitle: "Portal landing", icon: "🌐" },
  { key: "login", num: 2, title: "e-KYC & Auth", subtitle: "Aadhaar / OTP", icon: "🆔" },
  { key: "category", num: 3, title: "License Class", subtitle: "LMV / MCWG", icon: "🚗" },
  { key: "application", num: 4, title: "Zero-Form Dossier", subtitle: "DigiLocker verified", icon: "📋" },
  { key: "ll_test", num: 5, title: "LL Test", subtitle: "Online or Center", icon: "💻" },
  { key: "ll_issued", num: 6, title: "LL Issued", subtitle: "Digital Permit", icon: "📜" },
  { key: "practice", num: 7, title: "30-Day Practice", subtitle: "Safety Academy", icon: "🎯" },
  { key: "dl_booking", num: 8, title: "Track Slot", subtitle: "ADTT Booking", icon: "📅" },
  { key: "dl_test", num: 9, title: "DL Issued", subtitle: "Form 7 Smart Card", icon: "🏆" },
];

export function getActiveStepKey(stage: string, reviewOpen: boolean, categorySelected: boolean): JourneyStepKey {
  if (reviewOpen) return "application";
  switch (stage) {
    case "no_licence":
      return categorySelected ? "application" : "category";
    case "ll_application_submitted":
      return "application";
    case "ll_documents_verified":
    case "ll_test_scheduled":
      return "ll_test";
    case "ll_issued":
      return "ll_issued";
    case "practice_window":
      return "practice";
    case "dl_test_booked":
      return "dl_booking";
    case "dl_test_result_fail":
      return "practice";
    case "dl_test_result_pass":
    case "dl_issued":
      return "dl_test";
    default:
      return "intent";
  }
}

export function LandscapeJourneyMap({ currentStep }: { currentStep: JourneyStepKey }) {
  const currentIdx = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <nav className="landscape-journey-container" aria-label="Citizen Journey Roadmap">
      <div className="landscape-journey-scroll">
        <ol className="landscape-journey-steps">
          {STEPS.map((step, idx) => {
            const isDone = idx < currentIdx;
            const isCurrent = idx === currentIdx;
            return (
              <li
                key={step.key}
                className={`landscape-journey-step ${isDone ? "done" : ""} ${isCurrent ? "current" : ""}`}
              >
                <div className="landscape-step-marker">
                  {isDone ? "✓" : step.num}
                </div>
                <div className="landscape-step-content">
                  <span className="landscape-step-title">{step.title}</span>
                  <span className="landscape-step-sub">{step.subtitle}</span>
                </div>
                {idx < STEPS.length - 1 && <div className="landscape-step-connector" />}
              </li>
            );
          })}
        </ol>
      </div>
    </nav>
  );
}
