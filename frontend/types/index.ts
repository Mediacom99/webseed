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
  error_detail: string | null;
  vercel_url: string | null;
  primary_type: string | null;
  created_at: string;
  updated_at: string;
}

export interface BusinessDetail {
  id: string;
  place_id: string;
  name: string;
  address: string;
  phone: string | null;
  email: string | null;
  rating: number;
  reviews: number;
  category: string;
  maps_url: string | null;
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
  error_detail: string | null;
  vercel_url: string | null;
  site_screenshot_path: string | null;
  email_sent_at: string | null;
  test_iterations: number;
  test_issues: Record<string, unknown>[] | null;
  run_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface StatsResponse {
  [status: string]: number;
}

export interface SettingItem {
  key: string;
  value: string;
  description: string;
  updated_at: string;
}

export interface JobResponse {
  job_id: string;
}

export type SortDir = "asc" | "desc";

export type TabId = "all" | `job:${string}`;

export type StepStatus = "idle" | "running" | "done" | "error";

export interface PipelineStepStatus {
  step: PipelineStep;
  status: StepStatus;
}

export interface ActiveJob {
  jobId: string;
  startedAt: string;
  currentStep?: string;
}

export interface SearchRequest {
  location: string;
  query: string;
  types?: string[];
  limit?: number;
  min_score?: number;
  grid_size?: number;
}

export interface ToastItem {
  id: number;
  message: string;
  type: "success" | "error" | "info";
}
