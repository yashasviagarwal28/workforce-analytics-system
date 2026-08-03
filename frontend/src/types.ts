export type ReviewStatus =
  | "pending"
  | "confirmed_issue"
  | "legitimate"
  | "resolved";

export interface Anomaly {
  punch_id: string;
  shift_id: string;
  employee_id: string;
  department_id: string;
  clock_in: string;
  anomaly_score: number;
  predicted_anomaly: boolean;
  reason_hint: string;
  review_status: ReviewStatus;
  reviewer_notes?: string | null;
}

export interface AnomalyList {
  items: Anomaly[];
  total: number;
  limit: number;
  offset: number;
}

export interface Summary {
  total_records: number;
  flagged_records: number;
  pending_reviews: number;
  confirmed_issues: number;
}
