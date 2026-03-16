import { useMemo } from "react";
import { useWebSocketStore } from "@/stores/websocket";
import type { EventType, PipelineStep } from "@/types";

interface FilterOptions {
  jobId?: string;
  eventType?: EventType;
  step?: PipelineStep;
}

export function useWebSocketEvents(filters?: FilterOptions) {
  const events = useWebSocketStore((s) => s.events);

  return useMemo(() => {
    if (!filters) return events;

    return events.filter((event) => {
      if (filters.jobId && event.job_id !== filters.jobId) return false;
      if (filters.eventType && event.event_type !== filters.eventType)
        return false;
      if (filters.step && event.step !== filters.step) return false;
      return true;
    });
  }, [events, filters?.jobId, filters?.eventType, filters?.step]);
}
