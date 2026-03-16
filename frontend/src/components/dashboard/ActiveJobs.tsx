import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useWebSocketStore } from "@/stores/websocket";

export default function ActiveJobs() {
  const activeJobs = useWebSocketStore((s) => s.activeJobs);
  const jobs = Array.from(activeJobs.values());

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Active Jobs</CardTitle>
      </CardHeader>
      <CardContent>
        {jobs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No active jobs</p>
        ) : (
          <div className="space-y-2">
            {jobs.map((job) => (
              <div
                key={job.jobId}
                className="flex items-center justify-between rounded-md border p-2"
              >
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
                  <span className="font-mono text-sm">
                    {job.jobId.slice(0, 8)}...
                  </span>
                </div>
                {job.currentStep && (
                  <Badge variant="secondary">{job.currentStep}</Badge>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
