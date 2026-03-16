import { useState, useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, MoreHorizontal, Download } from "lucide-react";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import BusinessTable, {
  type BusinessRow,
} from "@/components/businesses/BusinessTable";
import StatusFilterChips, {
  filterKeyToStatuses,
} from "@/components/businesses/StatusFilterChips";
import BulkActionBar from "@/components/businesses/BulkActionBar";
import {
  useGetStatsBusinessesStatsGet,
  useListBusinessesBusinessesGet,
} from "@/api/endpoints/businesses/businesses";
import { useWebSocketStore } from "@/stores/websocket";

export default function BusinessesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchText, setSearchText] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

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

  const statuses = filterKeyToStatuses(statusParam);
  const apiStatus = statuses ? statuses.join(",") : undefined;

  // Get businesses for BulkActionBar context
  const { data: businessesData, refetch: refetchBusinesses } =
    useListBusinessesBusinessesGet(
      apiStatus ? { status: apiStatus } : undefined,
    );

  const businesses: BusinessRow[] = useMemo(() => {
    const raw = Array.isArray(businessesData?.data) ? businessesData.data : [];
    return raw.map((b: Record<string, unknown>) => ({
      place_id: b.place_id as string,
      name: (b.name as string) ?? "Unknown",
      status: (b.status as string) ?? "unknown",
      error_detail: b.error_detail as string | undefined,
      category: b.category as string | undefined,
      rating: b.rating as number | undefined,
      lead_score: b.lead_score as number | undefined,
      city: b.city as string | undefined,
      maps_url: b.maps_url as string | undefined,
    }));
  }, [businessesData]);

  const handleCsvExport = () => {
    const apiKey = localStorage.getItem("webseed-api-key");
    const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
    const url = `${baseUrl}/businesses/export/csv`;

    fetch(url, {
      headers: apiKey ? { "X-API-Key": apiKey } : {},
    })
      .then((r) => r.blob())
      .then((blob) => {
        const blobUrl = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = blobUrl;
        link.download = "businesses.csv";
        link.click();
        URL.revokeObjectURL(blobUrl);
      })
      .catch(() => toast.error("Failed to export CSV"));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Businesses</h1>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handleCsvExport}>
              <Download className="mr-2 h-4 w-4" />
              Export CSV
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

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

      <BulkActionBar
        selectedIds={selectedIds}
        businesses={businesses}
        onActionComplete={() => {
          setSelectedIds(new Set());
          void refetchBusinesses();
          void refetchStats();
        }}
      />
    </div>
  );
}
