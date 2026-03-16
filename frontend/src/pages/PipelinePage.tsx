import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import PipelineFlow from "@/components/pipeline/PipelineFlow";
import SearchForm from "@/components/pipeline/SearchForm";
import BusinessProgressTable from "@/components/pipeline/BusinessProgressTable";
import LiveActivityFeed from "@/components/pipeline/LiveActivityFeed";
import { usePipelineStatus } from "@/hooks/usePipelineStatus";

export default function PipelinePage() {
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const stepStatuses = usePipelineStatus(activeJobId);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Pipeline</h1>
      <PipelineFlow stepStatuses={stepStatuses} />

      <Card>
        <CardHeader>
          <CardTitle>Search</CardTitle>
        </CardHeader>
        <CardContent>
          <SearchForm onJobStarted={setActiveJobId} />
        </CardContent>
      </Card>

      <BusinessProgressTable jobId={activeJobId} />
      <LiveActivityFeed jobId={activeJobId} />
    </div>
  );
}
