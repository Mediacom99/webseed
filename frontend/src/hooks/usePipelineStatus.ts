import { useMemo } from "react";
import { useWebSocketStore } from "@/stores/websocket";
import type { PipelineStep } from "@/types";

export type StepStatus = "idle" | "running" | "done" | "error";

export interface PipelineStepStatus {
  step: PipelineStep;
  status: StepStatus;
}

const STEPS: PipelineStep[] = [
  "search",
  "enrich",
  "generate",
  "test",
  "deploy",
  "email",
];

export function usePipelineStatus(jobId: string | null): PipelineStepStatus[] {
  const events = useWebSocketStore((s) => s.events);

  return useMemo(() => {
    if (!jobId) {
      return STEPS.map((step) => ({ step, status: "idle" as StepStatus }));
    }

    const jobEvents = events.filter((e) => e.job_id === jobId);
    const stepStatuses = new Map<PipelineStep, StepStatus>();

    for (const event of jobEvents) {
      switch (event.event_type) {
        case "step_start":
          stepStatuses.set(event.step, "running");
          break;
        case "step_done":
          stepStatuses.set(event.step, "done");
          break;
        case "step_error":
          stepStatuses.set(event.step, "error");
          break;
      }
    }

    return STEPS.map((step) => ({
      step,
      status: stepStatuses.get(step) ?? "idle",
    }));
  }, [events, jobId]);
}
