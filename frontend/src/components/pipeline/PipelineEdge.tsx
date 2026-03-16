import { BaseEdge, getStraightPath } from "@xyflow/react";
import type { EdgeProps } from "@xyflow/react";

export default function PipelineEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  data,
}: EdgeProps) {
  const [edgePath] = getStraightPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  const isActive = (data as Record<string, unknown> | undefined)?.active === true;

  return (
    <BaseEdge
      id={id}
      path={edgePath}
      style={{
        stroke: isActive ? "#3b82f6" : "#d1d5db",
        strokeWidth: 2,
        strokeDasharray: isActive ? undefined : "5 5",
        animation: isActive ? "flowAnimation 1s linear infinite" : undefined,
      }}
    />
  );
}
