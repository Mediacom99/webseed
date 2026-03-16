export type PipelineStep =
  | "search"
  | "enrich"
  | "generate"
  | "test"
  | "deploy"
  | "email";

export type EventType =
  | "step_start"
  | "step_done"
  | "step_error"
  | "progress"
  | "cost"
  | "job_complete";

export interface PipelineEvent {
  event_type: EventType;
  job_id: string;
  step: PipelineStep;
  place_id?: string;
  message: string;
  data?: Record<string, unknown>;
  timestamp: string;
}

/** Summary of a business for list views. */
export interface BusinessSummary {
  id: string;
  place_id: string;
  name: string;
  address: string;
  category: string;
  rating: number;
  reviews: number;
  lead_score: number;
  status: string;
  error_detail: string;
  vercel_url: string;
  primary_type: string | null;
  created_at: string;
  updated_at: string;
}

/** Full business detail including all enrichment and pipeline fields. */
export interface BusinessDetail {
  id: string;
  place_id: string;
  name: string;
  address: string;
  phone: string | null;
  email: string;
  rating: number;
  reviews: number;
  category: string;
  maps_url: string;
  has_photos: boolean;
  photo_paths: string[];
  photo_refs: string[];
  fallback_unsplash_url: string;
  lead_score: number;
  price_level: string | null;
  business_status: string;
  primary_type: string | null;
  types: string[] | null;
  has_opening_hours: boolean;
  opening_hours_summary: string | null;
  accepts_credit_cards: boolean | null;
  editorial_summary: string | null;
  review_texts: string[] | null;
  status: string;
  error_detail: string;
  vercel_url: string;
  site_screenshot_path: string;
  email_sent_at: string;
  test_iterations: number;
  test_issues: Record<string, unknown>[];
  run_id: string;
  created_at: string;
  updated_at: string;
}

/** Stats response from GET /businesses/stats. */
export interface StatsResponse {
  [status: string]: number;
}

/** A single setting item (prompt or config). */
export interface SettingItem {
  key: string;
  value: string;
  description: string;
  updated_at: string;
}

/** Response from pipeline POST endpoints. */
export interface JobResponse {
  job_id: string;
}
