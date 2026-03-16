import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import ActiveJobs from "./ActiveJobs";
import { useWebSocketStore } from "@/stores/websocket";

describe("ActiveJobs", () => {
  beforeEach(() => {
    useWebSocketStore.setState({ activeJobs: new Map() });
  });

  it("shows empty state when no active jobs", () => {
    render(<ActiveJobs />);

    expect(screen.getByText("No active jobs")).toBeInTheDocument();
  });

  it("renders active jobs from store", () => {
    const activeJobs = new Map();
    activeJobs.set("abc12345-xxxx", {
      jobId: "abc12345-xxxx",
      startedAt: "2026-03-15T10:30:00.000Z",
      currentStep: "enrich",
    });

    useWebSocketStore.setState({ activeJobs });

    render(<ActiveJobs />);

    expect(screen.getByText("abc12345...")).toBeInTheDocument();
    expect(screen.getByText("enrich")).toBeInTheDocument();
  });
});
