// Module 1's API layer. All shared shapes come from types generated out of the
// backend OpenAPI schemas (AGENTS.md §4.3) — never hand-written duplicates.

import type { components as journeyComponents } from "./types/journey";
import type { components as academyComponents } from "./types/academy";

export type JourneyState = journeyComponents["schemas"]["JourneyState"];
export type VerifiedIdentityView = journeyComponents["schemas"]["VerifiedIdentityView"];
export type TestSlot = journeyComponents["schemas"]["TestSlot"];
export type VideoMatchResult = academyComponents["schemas"]["VideoMatchResult"];

export const JOURNEY_URL =
  import.meta.env.VITE_JOURNEY_URL ?? "http://localhost:8002";
export const GATEWAY_URL =
  import.meta.env.VITE_GATEWAY_URL ?? "http://localhost:8005";
export const ACADEMY_URL =
  import.meta.env.VITE_ACADEMY_URL ?? "http://localhost:8004";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: unknown,
  ) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    throw new ApiError(res.status, body && typeof body === "object" && "detail" in body ? (body as { detail: unknown }).detail : body);
  }
  return body as T;
}

export const journeyApi = {
  get: (applicantId: string) =>
    request<JourneyState>(`${JOURNEY_URL}/journey/${applicantId}`),
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
};

// Demo-only controls that stand in for the RTO's side of the mock gateway.
export const demoRtoApi = {
  verifyDocuments: (applicationNumber: string) =>
    request(`${GATEWAY_URL}/gov/applications/${applicationNumber}/verify-documents`, {
      method: "POST",
    }),
  reportTestResult: (
    applicationNumber: string,
    testType: "ll" | "dl",
    passed: boolean,
    failedCheckpoint?: string,
  ) =>
    request(`${GATEWAY_URL}/gov/test-results`, {
      method: "POST",
      body: JSON.stringify({
        application_number: applicationNumber,
        test_type: testType,
        passed,
        failed_checkpoint: failedCheckpoint ?? null,
      }),
    }),
};

export async function matchAcademyVideo(
  applicantId: string,
  query: string,
  journeyStage?: string,
): Promise<VideoMatchResult> {
  return request<VideoMatchResult>(`${ACADEMY_URL}/academy/match-video`, {
    method: "POST",
    body: JSON.stringify({
      applicant_id: applicantId,
      query,
      journey_stage: journeyStage ?? null,
    }),
  });
}
