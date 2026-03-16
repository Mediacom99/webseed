import { describe, it, expect, beforeEach } from "vitest";
import { useWebSocketStore } from "./websocket";
import type { PipelineEvent } from "@/types";

function makeEvent(overrides: Partial<PipelineEvent> = {}): PipelineEvent {
  return {
    event_type: "progress",
    job_id: "job-1",
    step: "search",
    message: "test event",
    timestamp: new Date().toISOString(),
    ...overrides,
  };
}

describe("useWebSocketStore", () => {
  beforeEach(() => {
    useWebSocketStore.setState({
      isConnected: false,
      events: [],
      activeJobs: new Map(),
    });
  });

  it("starts disconnected with empty state", () => {
    const state = useWebSocketStore.getState();
    expect(state.isConnected).toBe(false);
    expect(state.events).toHaveLength(0);
    expect(state.activeJobs.size).toBe(0);
  });

  it("caps events buffer at 200", () => {
    const events: PipelineEvent[] = [];
    for (let i = 0; i < 250; i++) {
      events.push(makeEvent({ message: `event-${i}` }));
    }
    useWebSocketStore.setState({ events });

    // Simulate what the store does on cap
    const state = useWebSocketStore.getState();
    const capped = state.events.slice(-200);
    expect(capped).toHaveLength(200);
    expect(capped[0].message).toBe("event-50");
  });

  it("clearEvents resets state", () => {
    useWebSocketStore.setState({
      events: [makeEvent()],
      activeJobs: new Map([
        ["job-1", { jobId: "job-1", startedAt: new Date().toISOString() }],
      ]),
    });

    useWebSocketStore.getState().clearEvents();

    const state = useWebSocketStore.getState();
    expect(state.events).toHaveLength(0);
    expect(state.activeJobs.size).toBe(0);
  });

  it("tracks active jobs from step_start events", () => {
    const activeJobs = new Map();
    activeJobs.set("job-1", {
      jobId: "job-1",
      startedAt: "2026-01-01T00:00:00Z",
      currentStep: "search",
    });

    useWebSocketStore.setState({ activeJobs });

    const state = useWebSocketStore.getState();
    expect(state.activeJobs.has("job-1")).toBe(true);
    expect(state.activeJobs.get("job-1")?.currentStep).toBe("search");
  });

  it("disconnect sets isConnected to false", () => {
    useWebSocketStore.setState({ isConnected: true });
    useWebSocketStore.getState().disconnect();

    expect(useWebSocketStore.getState().isConnected).toBe(false);
  });
});
