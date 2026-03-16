import { useEffect } from "react";
import { Link } from "react-router-dom";
import { AlertCircle, Ban, Database } from "lucide-react";
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

export default function SummaryRow() {
  const { data, refetch } = useGetStatsBusinessesStatsGet({
    query: { staleTime: 30_000 },
  });
  const events = useWebSocketStore((s) => s.events);

  const lastStepDone = events.findLast((e) => e.event_type === "step_done");
  useEffect(() => {
    if (lastStepDone) {
      void refetch();
    }
  }, [lastStepDone, refetch]);

  const stats = data?.data ?? {};

  const errorCount = ERROR_STATUSES.reduce(
    (sum, key) => sum + (stats[key] ?? 0),
    0,
  );
  const optedOut = stats["opted_out"] ?? 0;
  const total = Object.values(stats).reduce((sum, n) => sum + n, 0);

  return (
    <div className="flex flex-wrap items-center gap-4 text-sm">
      <Link
        to="/businesses?status=errors"
        className="flex items-center gap-1.5 text-red-600 hover:underline dark:text-red-400"
      >
        <AlertCircle className="h-4 w-4" />
        {errorCount} error{errorCount !== 1 ? "s" : ""}
      </Link>
      <span className="flex items-center gap-1.5 text-muted-foreground">
        <Ban className="h-4 w-4" />
        {optedOut} opted out
      </span>
      <span className="flex items-center gap-1.5 text-muted-foreground">
        <Database className="h-4 w-4" />
        {total} total
      </span>
    </div>
  );
}
