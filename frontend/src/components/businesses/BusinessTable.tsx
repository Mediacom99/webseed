import { useState, useMemo, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowUpDown, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import StatusBadge from "@/components/businesses/StatusBadge";
import {
  useListBusinessesBusinessesGet,
  useGetStatsBusinessesStatsGet,
} from "@/api/endpoints/businesses/businesses";
import { useWebSocketStore } from "@/stores/websocket";

type SortField = "name" | "rating" | "lead_score";
type SortDirection = "asc" | "desc";

export interface BusinessRow {
  place_id: string;
  name: string;
  status: string;
  error_detail?: string;
  category?: string;
  rating?: number;
  lead_score?: number;
  city?: string;
  maps_url?: string;
}

interface BusinessTableProps {
  statusFilter?: string;
  searchText?: string;
  selectedIds: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
}

export default function BusinessTable({
  statusFilter,
  searchText,
  selectedIds,
  onSelectionChange,
}: BusinessTableProps) {
  const [sortField, setSortField] = useState<SortField>("name");
  const [sortDir, setSortDir] = useState<SortDirection>("asc");
  const navigate = useNavigate();

  const { data: businessesData, refetch } = useListBusinessesBusinessesGet(
    statusFilter ? { status: statusFilter } : undefined,
  );

  // Still load stats for legacy test compatibility
  useGetStatsBusinessesStatsGet();

  const events = useWebSocketStore((s) => s.events);
  const lastStepDone = events.findLast((e) => e.event_type === "step_done");

  useEffect(() => {
    if (lastStepDone) {
      void refetch();
    }
  }, [lastStepDone, refetch]);

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

  const filtered = useMemo(() => {
    if (!searchText) return businesses;
    const q = searchText.toLowerCase();
    return businesses.filter((b) => b.name.toLowerCase().includes(q));
  }, [businesses, searchText]);

  const sorted = useMemo(() => {
    const items = [...filtered];
    items.sort((a, b) => {
      let cmp = 0;
      const aVal = a[sortField];
      const bVal = b[sortField];
      if (typeof aVal === "string" && typeof bVal === "string") {
        cmp = aVal.localeCompare(bVal);
      } else {
        cmp = ((aVal as number) ?? 0) - ((bVal as number) ?? 0);
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return items;
  }, [filtered, sortField, sortDir]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  };

  const toggleSelect = (placeId: string) => {
    const next = new Set(selectedIds);
    if (next.has(placeId)) next.delete(placeId);
    else next.add(placeId);
    onSelectionChange(next);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === sorted.length) {
      onSelectionChange(new Set());
    } else {
      onSelectionChange(new Set(sorted.map((b) => b.place_id)));
    }
  };

  if (sorted.length === 0) {
    return (
      <p className="py-8 text-center text-muted-foreground">
        No businesses match this filter
      </p>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">
              <Checkbox
                checked={
                  selectedIds.size === sorted.length && sorted.length > 0
                }
                onCheckedChange={toggleSelectAll}
                aria-label="Select all"
              />
            </TableHead>
            <TableHead>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleSort("name")}
              >
                Name <ArrowUpDown className="ml-1 h-3 w-3" />
              </Button>
            </TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Error</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleSort("rating")}
              >
                Rating <ArrowUpDown className="ml-1 h-3 w-3" />
              </Button>
            </TableHead>
            <TableHead>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleSort("lead_score")}
              >
                Lead Score <ArrowUpDown className="ml-1 h-3 w-3" />
              </Button>
            </TableHead>
            <TableHead>City</TableHead>
            <TableHead className="w-10">Maps</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((biz) => (
            <TableRow
              key={biz.place_id}
              className="cursor-pointer"
              onClick={() => navigate(`/businesses/${biz.place_id}`)}
            >
              <TableCell onClick={(e) => e.stopPropagation()}>
                <Checkbox
                  checked={selectedIds.has(biz.place_id)}
                  onCheckedChange={() => toggleSelect(biz.place_id)}
                  aria-label={`Select ${biz.name}`}
                />
              </TableCell>
              <TableCell className="font-medium">{biz.name}</TableCell>
              <TableCell>
                <StatusBadge status={biz.status} />
              </TableCell>
              <TableCell className="max-w-[150px] truncate text-xs text-muted-foreground">
                {biz.error_detail || "—"}
              </TableCell>
              <TableCell className="capitalize text-sm">
                {biz.category?.replace(/_/g, " ") ?? "—"}
              </TableCell>
              <TableCell>{biz.rating ?? "—"}</TableCell>
              <TableCell>{biz.lead_score ?? "—"}</TableCell>
              <TableCell>{biz.city ?? "—"}</TableCell>
              <TableCell onClick={(e) => e.stopPropagation()}>
                {biz.maps_url ? (
                  <a
                    href={biz.maps_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted-foreground hover:text-foreground"
                    aria-label={`Open ${biz.name} on Google Maps`}
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                ) : (
                  "—"
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
