import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";
import { motion } from "framer-motion";
import {
  Search,
  Database,
  Code2,
  TestTube2,
  Rocket,
  Mail,
  Loader2,
  CheckCircle2,
  XCircle,
  Circle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { StepStatus } from "@/hooks/usePipelineStatus";
import type { PipelineStep } from "@/types";

const STEP_ICONS: Record<PipelineStep, React.ElementType> = {
  search: Search,
  enrich: Database,
  generate: Code2,
  test: TestTube2,
  deploy: Rocket,
  email: Mail,
};

const STATUS_STYLES: Record<StepStatus, string> = {
  idle: "border-border bg-card text-muted-foreground",
  running: "border-blue-500 bg-blue-50 text-blue-700",
  done: "border-green-500 bg-green-50 text-green-700",
  error: "border-red-500 bg-red-50 text-red-700",
};

const STATUS_ICONS: Record<StepStatus, React.ElementType> = {
  idle: Circle,
  running: Loader2,
  done: CheckCircle2,
  error: XCircle,
};

export interface PipelineNodeData {
  label: string;
  step: PipelineStep;
  status: StepStatus;
  [key: string]: unknown;
}

function PipelineNode({ data }: NodeProps) {
  const nodeData = data as PipelineNodeData;
  const StepIcon = STEP_ICONS[nodeData.step];
  const StatusIcon = STATUS_ICONS[nodeData.status];

  return (
    <motion.div
      className={cn(
        "flex w-36 flex-col items-center gap-2 rounded-lg border-2 p-4 shadow-sm",
        STATUS_STYLES[nodeData.status],
      )}
      animate={{
        scale: nodeData.status === "running" ? [1, 1.02, 1] : 1,
      }}
      transition={{
        duration: 1.5,
        repeat: nodeData.status === "running" ? Infinity : 0,
      }}
    >
      <Handle type="target" position={Position.Left} className="invisible" />
      <StepIcon className="h-6 w-6" />
      <span className="text-sm font-medium capitalize">{nodeData.label}</span>
      <StatusIcon
        className={cn(
          "h-4 w-4",
          nodeData.status === "running" && "animate-spin",
        )}
      />
      <Handle type="source" position={Position.Right} className="invisible" />
    </motion.div>
  );
}

export default memo(PipelineNode);
