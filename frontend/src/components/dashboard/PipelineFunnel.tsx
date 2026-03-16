import { useEffect } from "react";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useGetStatsBusinessesStatsGet } from "@/api/endpoints/businesses/businesses";
import { useWebSocketStore } from "@/stores/websocket";

const FUNNEL_STEPS = [
  { key: "searched", label: "Search", runningKey: "running_search" },
  { key: "enriched", label: "Enrich", runningKey: "running_enrich" },
  { key: "generated", label: "Generate", runningKey: "running_generate" },
  { key: "tested", label: "Test", runningKey: "running_test" },
  { key: "deployed", label: "Deploy", runningKey: "running_deploy" },
  { key: "emailed", label: "Email", runningKey: "running_email" },
] as const;

function getCountForStep(
  stats: Record<string, number>,
  stepKey: string,
): number {
  // Count includes the step status plus all statuses that come after it
  // But for funnel, we show the count at exactly that status
  return stats[stepKey] ?? 0;
}

function getRunningCount(
  stats: Record<string, number>,
  runningKey: string,
): number {
  return stats[runningKey] ?? 0;
}

export default function PipelineFunnel() {
  const { data, isLoading, refetch } = useGetStatsBusinessesStatsGet({
    query: { staleTime: 30_000 },
  });
  const events = useWebSocketStore((s) => s.events);

  const lastStepDone = events.findLast((e) => e.event_type === "step_done");
  useEffect(() => {
    if (lastStepDone) {
      void refetch();
    }
  }, [lastStepDone, refetch]);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center gap-2 overflow-x-auto p-4">
          {FUNNEL_STEPS.map((step) => (
            <div key={step.key} className="flex items-center gap-2">
              <Skeleton className="h-16 w-24 rounded-lg" />
              {step.key !== "emailed" && <Skeleton className="h-4 w-4" />}
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  const stats = data?.data ?? {};
  const total = Object.values(stats).reduce(
    (sum: number, n: number) => sum + n,
    0,
  );

  if (total === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center p-8 text-center">
          <p className="text-muted-foreground">
            No businesses yet — start with a search
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="flex items-center gap-2 overflow-x-auto p-4">
        {FUNNEL_STEPS.map((step, i) => {
          const count = getCountForStep(stats, step.key);
          const running = getRunningCount(stats, step.runningKey);
          return (
            <div key={step.key} className="flex items-center gap-2">
              <div
                className={cn(
                  "flex min-w-[6rem] flex-col items-center rounded-lg border p-3 text-center transition-colors",
                  running > 0
                    ? "border-blue-300 bg-blue-50 dark:border-blue-700 dark:bg-blue-950"
                    : "border-border",
                )}
              >
                <span className="text-xs font-medium text-muted-foreground">
                  {step.label}
                </span>
                <span className="text-xl font-bold">{count}</span>
                {running > 0 && (
                  <span className="text-xs text-blue-600 dark:text-blue-400 animate-pulse">
                    +{running} running
                  </span>
                )}
              </div>
              {i < FUNNEL_STEPS.length - 1 && (
                <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground" />
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
