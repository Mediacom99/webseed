import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import PipelineFlow from "./PipelineFlow";
import type { PipelineStepStatus } from "@/hooks/usePipelineStatus";

// Mock ReactFlow since it needs a browser-like environment with ResizeObserver
vi.mock("@xyflow/react", () => {
  const MockReactFlow = ({
    nodes,
    edges,
  }: {
    nodes: Array<{ id: string; data: { label: string } }>;
    edges: Array<{ id: string }>;
  }) => (
    <div data-testid="react-flow">
      {nodes.map((n) => (
        <div key={n.id} data-testid={`node-${n.id}`}>
          {n.data.label}
        </div>
      ))}
      {edges.map((e) => (
        <div key={e.id} data-testid={`edge-${e.id}`} />
      ))}
    </div>
  );

  return {
    ReactFlow: MockReactFlow,
    Handle: () => null,
    Position: { Left: "left", Right: "right" },
    BaseEdge: () => null,
    getStraightPath: () => [""],
  };
});

const defaultStatuses: PipelineStepStatus[] = [
  { step: "search", status: "idle" },
  { step: "enrich", status: "idle" },
  { step: "generate", status: "idle" },
  { step: "test", status: "idle" },
  { step: "deploy", status: "idle" },
  { step: "email", status: "idle" },
];

describe("PipelineFlow", () => {
  it("renders 6 nodes and 5 edges", () => {
    render(<PipelineFlow stepStatuses={defaultStatuses} />);

    expect(screen.getByTestId("node-search")).toBeInTheDocument();
    expect(screen.getByTestId("node-enrich")).toBeInTheDocument();
    expect(screen.getByTestId("node-generate")).toBeInTheDocument();
    expect(screen.getByTestId("node-test")).toBeInTheDocument();
    expect(screen.getByTestId("node-deploy")).toBeInTheDocument();
    expect(screen.getByTestId("node-email")).toBeInTheDocument();

    expect(screen.getByTestId("edge-search-enrich")).toBeInTheDocument();
    expect(screen.getByTestId("edge-enrich-generate")).toBeInTheDocument();
    expect(screen.getByTestId("edge-generate-test")).toBeInTheDocument();
    expect(screen.getByTestId("edge-test-deploy")).toBeInTheDocument();
    expect(screen.getByTestId("edge-deploy-email")).toBeInTheDocument();
  });

  it("renders step labels", () => {
    render(<PipelineFlow stepStatuses={defaultStatuses} />);

    expect(screen.getByText("search")).toBeInTheDocument();
    expect(screen.getByText("enrich")).toBeInTheDocument();
    expect(screen.getByText("generate")).toBeInTheDocument();
    expect(screen.getByText("test")).toBeInTheDocument();
    expect(screen.getByText("deploy")).toBeInTheDocument();
    expect(screen.getByText("email")).toBeInTheDocument();
  });
});
