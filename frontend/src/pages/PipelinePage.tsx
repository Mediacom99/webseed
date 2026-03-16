import { useState } from "react";
import PipelineFlow from "@/components/pipeline/PipelineFlow";
import { usePipelineStatus } from "@/hooks/usePipelineStatus";

export default function PipelinePage() {
  const [activeJobId] = useState<string | null>(null);
  const stepStatuses = usePipelineStatus(activeJobId);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Pipeline</h1>
      <PipelineFlow stepStatuses={stepStatuses} />
    </div>
  );
}
