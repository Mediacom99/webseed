import { ArrowRight, Check, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const PIPELINE_NODES = [
  { key: "searched", label: "Search" },
  { key: "enriched", label: "Enrich" },
  { key: "generated", label: "Generate" },
  { key: "tested", label: "Test" },
  { key: "deployed", label: "Deploy" },
  { key: "emailed", label: "Email" },
] as const;

const STATUS_ORDER: Record<string, number> = {
  searched: 0,
  enriched: 1,
  generated: 2,
  tested: 3,
  deployed: 4,
  email_queued: 5,
  emailed: 5,
  running_enrich: 1,
  running_generate: 2,
  running_test: 3,
  running_deploy: 4,
  running_email: 5,
  error_enrich: 1,
  error_generate: 2,
  error_test: 3,
  error_deploy: 4,
  error_email: 5,
  error_run: 0,
  opted_out: -1,
};

type NodeState = "completed" | "running" | "error" | "current" | "future";

function getNodeState(nodeIndex: number, status: string): NodeState {
  const statusIndex = STATUS_ORDER[status] ?? -1;

  if (status.startsWith("running_")) {
    if (nodeIndex < statusIndex) return "completed";
    if (nodeIndex === statusIndex) return "running";
    return "future";
  }

  if (status.startsWith("error_")) {
    if (nodeIndex < statusIndex) return "completed";
    if (nodeIndex === statusIndex) return "error";
    return "future";
  }

  if (nodeIndex < statusIndex) return "completed";
  if (nodeIndex === statusIndex) return "current";
  return "future";
}

const NODE_STYLES: Record<NodeState, string> = {
  completed: "border-green-500 bg-green-50 dark:bg-green-950 text-green-700",
  running: "border-blue-500 bg-blue-50 dark:bg-blue-950 text-blue-700",
  error: "border-red-500 bg-red-50 dark:bg-red-950 text-red-700",
  current: "border-primary bg-primary/10 text-primary ring-2 ring-primary/20",
  future: "border-muted bg-muted/30 text-muted-foreground",
};

interface PipelineGraphProps {
  status: string;
}

export default function PipelineGraph({ status }: PipelineGraphProps) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto py-2">
      {PIPELINE_NODES.map((node, i) => {
        const state = getNodeState(i, status);
        return (
          <div key={node.key} className="flex items-center gap-2">
            <div
              className={cn(
                "flex min-w-[5rem] flex-col items-center rounded-lg border-2 p-2.5 text-center transition-colors",
                NODE_STYLES[state],
              )}
            >
              <div className="mb-1">
                {state === "completed" && (
                  <Check className="h-4 w-4 text-green-600" />
                )}
                {state === "running" && (
                  <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                )}
                {state === "error" && (
                  <X className="h-4 w-4 text-red-600" />
                )}
              </div>
              <span className="text-xs font-medium">{node.label}</span>
            </div>
            {i < PIPELINE_NODES.length - 1 && (
              <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground" />
            )}
          </div>
        );
      })}
    </div>
  );
}
