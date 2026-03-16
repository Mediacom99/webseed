import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import RecentActivity from "./RecentActivity";
import { useWebSocketStore } from "@/stores/websocket";
import type { PipelineEvent } from "@/types";

function makeEvent(overrides: Partial<PipelineEvent> = {}): PipelineEvent {
  return {
    event_type: "progress",
    job_id: "job-1",
    step: "search",
    message: "Searching...",
    timestamp: "2026-03-15T10:30:00.000Z",
    ...overrides,
  };
}

describe("RecentActivity", () => {
  beforeEach(() => {
    useWebSocketStore.setState({ events: [] });
  });

  it("shows empty state when no events", () => {
    render(<RecentActivity />);

    expect(screen.getByText("No recent activity")).toBeInTheDocument();
  });

  it("renders event list from WS store", () => {
    useWebSocketStore.setState({
      events: [
        makeEvent({ message: "Found 5 businesses", step: "search" }),
        makeEvent({
          message: "Enriching business",
          step: "enrich",
          event_type: "step_start",
        }),
      ],
    });

    render(<RecentActivity />);

    expect(
      screen.getByText("[search] Found 5 businesses"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("[enrich] Enriching business"),
    ).toBeInTheDocument();
  });
});
