import { useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useGetStatsBusinessesStatsGet } from "@/api/endpoints/businesses/businesses";
import { useWebSocketStore } from "@/stores/websocket";

const ERROR_STATUSES = [
  "error_enrich",
  "error_generate",
  "error_test",
  "error_deploy",
  "error_email",
  "error_run",
];

const SITE_STATUSES = ["deployed", "email_queued", "emailed"];

function pct(count: number, total: number): string {
  if (total === 0) return "0%";
  return `${Math.round((count / total) * 100)}%`;
}

export default function StatsCards() {
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
        <CardHeader>
          <Skeleton className="h-4 w-20" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-6 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const stats = data?.data ?? {};
  const total = Object.values(stats).reduce((sum, n) => sum + n, 0);
  const withSites = SITE_STATUSES.reduce(
    (sum, key) => sum + (stats[key] ?? 0),
    0,
  );
  const errors = ERROR_STATUSES.reduce(
    (sum, key) => sum + (stats[key] ?? 0),
    0,
  );
  const blacklisted = stats["opted_out"] ?? 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Stats</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            Total businesses
          </span>
          <span className="font-semibold">{total}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">With sites</span>
          <span className="font-semibold">
            {withSites}{" "}
            <span className="text-xs text-muted-foreground">
              ({pct(withSites, total)})
            </span>
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Errors</span>
          <span className="font-semibold text-red-600 dark:text-red-400">
            {errors}{" "}
            <span className="text-xs text-muted-foreground">
              ({pct(errors, total)})
            </span>
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Blacklisted</span>
          <span className="font-semibold">{blacklisted}</span>
        </div>
      </CardContent>
    </Card>
  );
}
