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
