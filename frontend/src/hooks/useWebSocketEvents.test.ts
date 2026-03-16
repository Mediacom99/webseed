import { renderHook } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import { useWebSocketEvents } from "./useWebSocketEvents";
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

describe("useWebSocketEvents", () => {
  beforeEach(() => {
    useWebSocketStore.setState({ events: [] });
  });

  it("returns all events when no filters", () => {
    const events = [makeEvent(), makeEvent({ job_id: "job-2" })];
    useWebSocketStore.setState({ events });

    const { result } = renderHook(() => useWebSocketEvents());
    expect(result.current).toHaveLength(2);
  });

  it("filters by jobId", () => {
    const events = [
      makeEvent({ job_id: "job-1" }),
      makeEvent({ job_id: "job-2" }),
      makeEvent({ job_id: "job-1" }),
    ];
    useWebSocketStore.setState({ events });

    const { result } = renderHook(() =>
      useWebSocketEvents({ jobId: "job-1" }),
    );
    expect(result.current).toHaveLength(2);
    expect(result.current.every((e) => e.job_id === "job-1")).toBe(true);
  });

  it("filters by eventType", () => {
    const events = [
      makeEvent({ event_type: "step_start" }),
      makeEvent({ event_type: "step_done" }),
      makeEvent({ event_type: "step_start" }),
    ];
    useWebSocketStore.setState({ events });

    const { result } = renderHook(() =>
      useWebSocketEvents({ eventType: "step_start" }),
    );
    expect(result.current).toHaveLength(2);
  });

  it("filters by step", () => {
    const events = [
      makeEvent({ step: "search" }),
      makeEvent({ step: "enrich" }),
      makeEvent({ step: "search" }),
    ];
    useWebSocketStore.setState({ events });

    const { result } = renderHook(() =>
      useWebSocketEvents({ step: "search" }),
    );
    expect(result.current).toHaveLength(2);
  });

  it("combines multiple filters", () => {
    const events = [
      makeEvent({ job_id: "job-1", event_type: "step_start", step: "search" }),
      makeEvent({ job_id: "job-1", event_type: "step_done", step: "search" }),
      makeEvent({ job_id: "job-2", event_type: "step_start", step: "search" }),
    ];
    useWebSocketStore.setState({ events });

    const { result } = renderHook(() =>
      useWebSocketEvents({ jobId: "job-1", eventType: "step_start" }),
    );
    expect(result.current).toHaveLength(1);
  });
});
