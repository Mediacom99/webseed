import { renderHook } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import { usePipelineStatus } from "./usePipelineStatus";
import { useWebSocketStore } from "@/stores/websocket";
import type { PipelineEvent } from "@/types";

function makeEvent(overrides: Partial<PipelineEvent> = {}): PipelineEvent {
  return {
    event_type: "progress",
    job_id: "job-1",
    step: "search",
    message: "test",
    timestamp: new Date().toISOString(),
    ...overrides,
  };
}

describe("usePipelineStatus", () => {
  beforeEach(() => {
    useWebSocketStore.setState({ events: [] });
  });

  it("returns all steps as idle when no jobId", () => {
    const { result } = renderHook(() => usePipelineStatus(null));

    expect(result.current).toHaveLength(6);
    expect(result.current.every((s) => s.status === "idle")).toBe(true);
    expect(result.current.map((s) => s.step)).toEqual([
      "search",
      "enrich",
      "generate",
      "test",
      "deploy",
      "email",
    ]);
  });

  it("returns all steps as idle when no events for jobId", () => {
    useWebSocketStore.setState({
      events: [makeEvent({ job_id: "other-job" })],
    });

    const { result } = renderHook(() => usePipelineStatus("job-1"));
    expect(result.current.every((s) => s.status === "idle")).toBe(true);
  });

  it("derives correct statuses from event sequence", () => {
    useWebSocketStore.setState({
      events: [
        makeEvent({
          job_id: "job-1",
          step: "search",
          event_type: "step_start",
        }),
        makeEvent({
          job_id: "job-1",
          step: "search",
          event_type: "step_done",
        }),
        makeEvent({
          job_id: "job-1",
          step: "enrich",
          event_type: "step_start",
        }),
        makeEvent({
          job_id: "job-1",
          step: "generate",
          event_type: "step_error",
        }),
      ],
    });

    const { result } = renderHook(() => usePipelineStatus("job-1"));

    const statusMap = new Map(result.current.map((s) => [s.step, s.status]));
    expect(statusMap.get("search")).toBe("done");
    expect(statusMap.get("enrich")).toBe("running");
    expect(statusMap.get("generate")).toBe("error");
    expect(statusMap.get("test")).toBe("idle");
    expect(statusMap.get("deploy")).toBe("idle");
    expect(statusMap.get("email")).toBe("idle");
  });
});
