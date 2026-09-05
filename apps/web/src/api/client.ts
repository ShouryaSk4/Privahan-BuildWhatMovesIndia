// Module 1's API layer. All shared shapes come from types generated out of the
// backend OpenAPI schemas (AGENTS.md §4.3) — never hand-written duplicates.

import type { components as journeyComponents } from "./types/journey";
import type { components as academyComponents } from "./types/academy";

export type JourneyState = journeyComponents["schemas"]["JourneyState"];
export type VerifiedIdentityView = journeyComponents["schemas"]["VerifiedIdentityView"];
export type TestSlot = journeyComponents["schemas"]["TestSlot"];
export type ExamPaper = journeyComponents["schemas"]["ExamPaper"];
export type ExamOutcome = journeyComponents["schemas"]["ExamOutcome"];
export type VideoMatchResult = academyComponents["schemas"]["VideoMatchResult"];

const isDev = import.meta.env.DEV;

export const JOURNEY_URL =
  import.meta.env.VITE_JOURNEY_URL ?? (isDev ? "http://localhost:8002" : "");
// Module 4 & 6 have no CORS for the browser, so dev proxies /api/* and prod
// routes them through api/index.py.
export const ACADEMY_URL =
  import.meta.env.VITE_ACADEMY_URL ?? (isDev ? "/api/academy" : "/academy");
export const BOL_URL =
  import.meta.env.VITE_BOL_URL ?? (isDev ? "http://localhost:8006" : "/bol");

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: unknown,
  ) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
}

// -- session token -----------------------------------------------------------
// The government/journey endpoints are now ownership-gated: a session token
// binds this browser to one applicant_id, and every /journey call carries it.
let sessionToken: string | null = null;

export function clearSession(): void {
  sessionToken = null;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (sessionToken && url.startsWith(JOURNEY_URL)) {
    headers.Authorization = `Bearer ${sessionToken}`;
  }
  const res = await fetch(url, { ...init, headers });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    throw new ApiError(
      res.status,
      body && typeof body === "object" && "detail" in body
        ? (body as { detail: unknown }).detail
        : body,
    );
  }
  return body as T;
}

/** Mint a session bound to this applicant. Call before any journey request. */
export async function startSession(applicantId: string): Promise<void> {
  const res = await request<{ token: string }>(`${JOURNEY_URL}/session`, {
    method: "POST",
    body: JSON.stringify({ applicant_id: applicantId }),
  });
  sessionToken = res.token;
}

export const journeyApi = {
  get: (applicantId: string) =>
    request<JourneyState>(`${JOURNEY_URL}/journey/${applicantId}`),
  reset: (applicantId: string) =>
    request<JourneyState>(`${JOURNEY_URL}/journey/${applicantId}/reset`, {
      method: "POST",
    }),
  verifiedProfile: (applicantId: string) =>
    request<VerifiedIdentityView>(
      `${JOURNEY_URL}/journey/${applicantId}/verified-profile`,
    ),
  apply: (applicantId: string, confirmedRtoCode?: string) =>
    request<JourneyState>(`${JOURNEY_URL}/journey/${applicantId}/apply`, {
      method: "POST",
      body: JSON.stringify({ confirmed_rto_code: confirmedRtoCode ?? null }),
    }),
  event: (applicantId: string, event: string) =>
    request<JourneyState>(`${JOURNEY_URL}/journey/${applicantId}/events`, {
      method: "POST",
      body: JSON.stringify({ event }),
    }),
  sync: (applicantId: string) =>
    request<JourneyState>(`${JOURNEY_URL}/journey/${applicantId}/sync`, {
      method: "POST",
    }),
  slots: (applicantId: string) =>
    request<TestSlot[]>(`${JOURNEY_URL}/journey/${applicantId}/dl-test/slots`),
  book: (applicantId: string, slotId: string) =>
    request<JourneyState>(
      `${JOURNEY_URL}/journey/${applicantId}/dl-test/bookings`,
      { method: "POST", body: JSON.stringify({ slot_id: slotId }) },
    ),
  // Server-authoritative learner's test.
  getExam: (applicantId: string) =>
    request<ExamPaper>(`${JOURNEY_URL}/journey/${applicantId}/ll-exam`),
  submitExam: (
    applicantId: string,
    answers: (number | null)[],
    integrity?: { camera: string; events: unknown[] },
  ) =>
    request<ExamOutcome>(`${JOURNEY_URL}/journey/${applicantId}/ll-exam`, {
      method: "POST",
      body: JSON.stringify({ answers, integrity: integrity ?? null }),
    }),
  // Demo stand-in for the RTO reporting a physical driving-test result — routed
  // through the token-checked journey service, never the raw gov endpoint.
  simulateDlResult: (applicantId: string, passed: boolean, failedCheckpoint?: string) =>
    request<JourneyState>(
      `${JOURNEY_URL}/journey/${applicantId}/simulate/dl-result`,
      {
        method: "POST",
        body: JSON.stringify({ passed, failed_checkpoint: failedCheckpoint ?? null }),
      },
    ),
};

export interface AcademyAskResponse {
  query: string;
  answer: string;
  source_sections: string[];
  matched_video?: VideoMatchResult | null;
}

export async function matchAcademyVideo(
  applicantId: string,
  query: string,
  journeyStage?: string,
): Promise<VideoMatchResult> {
  return request<VideoMatchResult>(`${ACADEMY_URL}/match-video`, {
    method: "POST",
    body: JSON.stringify({
      applicant_id: applicantId,
      query,
      journey_stage: journeyStage ?? null,
    }),
  });
}

export async function askAcademyManual(
  applicantId: string,
  query: string,
  journeyStage?: string,
): Promise<AcademyAskResponse> {
  return request<AcademyAskResponse>(`${ACADEMY_URL}/ask`, {
    method: "POST",
    body: JSON.stringify({
      applicant_id: applicantId,
      query,
      journey_stage: journeyStage ?? null,
    }),
  });
}
