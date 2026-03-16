import { useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useGetStatsBusinessesStatsGet } from "@/api/endpoints/businesses/businesses";
import { useWebSocketStore } from "@/stores/websocket";

const STATUS_COLORS: Record<string, string> = {
  searched: "bg-blue-100 text-blue-800",
  enriched: "bg-purple-100 text-purple-800",
  generated: "bg-green-100 text-green-800",
  tested: "bg-teal-100 text-teal-800",
  deployed: "bg-emerald-100 text-emerald-800",
  email_queued: "bg-amber-100 text-amber-800",
  emailed: "bg-indigo-100 text-indigo-800",
  error_enrich: "bg-red-100 text-red-800",
  error_generate: "bg-red-100 text-red-800",
  error_test: "bg-red-100 text-red-800",
  error_deploy: "bg-red-100 text-red-800",
  error_email: "bg-red-100 text-red-800",
  error_run: "bg-red-100 text-red-800",
  opted_out: "bg-gray-100 text-gray-800",
};

export default function StatsCards() {
  const { data, refetch } = useGetStatsBusinessesStatsGet({
    query: { staleTime: 30_000 },
  });
  const events = useWebSocketStore((s) => s.events);

  // Refetch when step_done events arrive
  const lastStepDone = events.findLast((e) => e.event_type === "step_done");
  useEffect(() => {
    if (lastStepDone) {
      void refetch();
    }
  }, [lastStepDone, refetch]);

  const stats = data?.data;

  if (!stats) return null;

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
      {Object.entries(stats).map(([status, count]) => (
        <Card key={status}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium capitalize">
              {status.replace(/_/g, " ")}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <span className="text-2xl font-bold">{count}</span>
            <Badge
              variant="secondary"
              className={STATUS_COLORS[status] ?? ""}
            >
              {status}
            </Badge>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
