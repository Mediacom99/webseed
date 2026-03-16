import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import BusinessProgressTable from "./BusinessProgressTable";
import { useWebSocketStore } from "@/stores/websocket";
import type { PipelineEvent } from "@/types";

function makeEvent(overrides: Partial<PipelineEvent> = {}): PipelineEvent {
  return {
    event_type: "step_done",
    job_id: "job-1",
    step: "search",
    place_id: "ChIJ123456789",
    message: "Done",
    timestamp: "2026-03-15T10:30:00.000Z",
    data: { name: "Ristorante Roma" },
    ...overrides,
  };
}

describe("BusinessProgressTable", () => {
  beforeEach(() => {
    useWebSocketStore.setState({ events: [] });
  });

  it("shows empty state when no businesses", () => {
    render(<BusinessProgressTable jobId={null} />);
    expect(
      screen.getByText("No businesses in this job"),
    ).toBeInTheDocument();
  });

  it("renders rows from WS events", () => {
    useWebSocketStore.setState({
      events: [
        makeEvent({
          place_id: "ChIJ123456789",
          event_type: "step_done",
          step: "search",
          data: { name: "Ristorante Roma" },
        }),
      ],
    });

    render(<BusinessProgressTable jobId="job-1" />);

    expect(screen.getByText("Ristorante Roma")).toBeInTheDocument();
    expect(screen.getByText("ChIJ12345678...")).toBeInTheDocument();
  });
});
