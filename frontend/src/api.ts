import axios from "axios";
import type { Anomaly, AnomalyList, ReviewStatus, Summary } from "./types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

export async function fetchSummary(): Promise<Summary> {
  const response = await api.get<Summary>("/metrics/summary");
  return response.data;
}

export async function fetchAnomalies(): Promise<AnomalyList> {
  const response = await api.get<AnomalyList>("/anomalies", {
    params: { flagged_only: true, limit: 100 },
  });
  return response.data;
}

export async function updateReview(
  punchId: string,
  reviewStatus: ReviewStatus,
  reviewerNotes?: string,
): Promise<Anomaly> {
  const response = await api.patch<Anomaly>(`/anomalies/${punchId}`, {
    review_status: reviewStatus,
    reviewer_notes: reviewerNotes || null,
  });
  return response.data;
}
