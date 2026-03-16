import { useMemo } from "react";
import { ReactFlow, type Node, type Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import PipelineNode from "./PipelineNode";
import PipelineEdge from "./PipelineEdge";
import type { PipelineStepStatus } from "@/hooks/usePipelineStatus";
import type { PipelineStep } from "@/types";

const nodeTypes = { pipeline: PipelineNode };
const edgeTypes = { pipeline: PipelineEdge };

const STEPS: PipelineStep[] = [
  "search",
  "enrich",
  "generate",
  "test",
  "deploy",
  "email",
];

interface PipelineFlowProps {
  stepStatuses: PipelineStepStatus[];
}

export default function PipelineFlow({ stepStatuses }: PipelineFlowProps) {
  const statusMap = useMemo(() => {
    const map = new Map<string, PipelineStepStatus>();
    for (const s of stepStatuses) {
      map.set(s.step, s);
    }
    return map;
  }, [stepStatuses]);

  const nodes: Node[] = useMemo(
    () =>
      STEPS.map((step, i) => ({
        id: step,
        type: "pipeline",
        position: { x: i * 200, y: 0 },
        data: {
          label: step,
          step,
          status: statusMap.get(step)?.status ?? "idle",
        },
        draggable: false,
      })),
    [statusMap],
  );

  const edges: Edge[] = useMemo(
    () =>
      STEPS.slice(0, -1).map((step, i) => {
        const sourceStatus = statusMap.get(step)?.status;
        return {
          id: `${step}-${STEPS[i + 1]}`,
          source: step,
          target: STEPS[i + 1],
          type: "pipeline",
          data: { active: sourceStatus === "running" },
        };
      }),
    [statusMap],
  );

  return (
    <div className="h-48 w-full rounded-lg border bg-card">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        proOptions={{ hideAttribution: true }}
      />
    </div>
  );
}
