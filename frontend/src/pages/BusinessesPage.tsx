import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import BusinessTable from "@/components/businesses/BusinessTable";
import StatusFilterChips, {
  filterKeyToStatuses,
} from "@/components/businesses/StatusFilterChips";
import { useGetStatsBusinessesStatsGet } from "@/api/endpoints/businesses/businesses";
import { useWebSocketStore } from "@/stores/websocket";

export default function BusinessesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchText, setSearchText] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // URL-driven status filter
  const statusParam = searchParams.get("status") ?? "all";
  const setStatusFilter = (filter: string) => {
    if (filter === "all") {
      searchParams.delete("status");
    } else {
      searchParams.set("status", filter);
    }
    setSearchParams(searchParams, { replace: true });
    setSelectedIds(new Set());
  };

  const { data: statsData, refetch: refetchStats } =
    useGetStatsBusinessesStatsGet({ query: { staleTime: 30_000 } });

  const events = useWebSocketStore((s) => s.events);
  const lastStepDone = events.findLast((e) => e.event_type === "step_done");
  useEffect(() => {
    if (lastStepDone) {
      void refetchStats();
    }
  }, [lastStepDone, refetchStats]);

  const stats = (statsData?.data as Record<string, number>) ?? {};

  // Convert filter key to status string for API
  const statuses = filterKeyToStatuses(statusParam);
  const apiStatus = statuses ? statuses.join(",") : undefined;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Businesses</h1>

      <StatusFilterChips
        stats={stats}
        activeFilter={statusParam}
        onFilterChange={setStatusFilter}
      />

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search by name..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          className="pl-9"
        />
      </div>

      <BusinessTable
        statusFilter={apiStatus}
        searchText={searchText}
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
      />
    </div>
  );
}
