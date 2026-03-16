import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import LiveActivityFeed from "./LiveActivityFeed";
import { useWebSocketStore } from "@/stores/websocket";
import type { PipelineEvent } from "@/types";

function makeEvent(overrides: Partial<PipelineEvent> = {}): PipelineEvent {
  return {
    event_type: "progress",
    job_id: "job-1",
    step: "search",
    message: "Searching businesses",
    timestamp: "2026-03-15T10:30:00.000Z",
    ...overrides,
  };
}

describe("LiveActivityFeed", () => {
  beforeEach(() => {
    useWebSocketStore.setState({ events: [] });
  });

  it("shows empty state when no events", () => {
    render(<LiveActivityFeed jobId={null} />);
    expect(
      screen.getByText("No events yet. Start a job to see activity."),
    ).toBeInTheDocument();
  });

  it("renders events for the given job", () => {
    useWebSocketStore.setState({
      events: [
        makeEvent({ job_id: "job-1", message: "Found 5 businesses" }),
        makeEvent({ job_id: "job-2", message: "Other job event" }),
      ],
    });

    render(<LiveActivityFeed jobId="job-1" />);

    expect(
      screen.getByText("[search] Found 5 businesses"),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("[search] Other job event"),
    ).not.toBeInTheDocument();
  });
});
