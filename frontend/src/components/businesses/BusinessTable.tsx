import { useState, useMemo, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import StatusBadge from "@/components/businesses/StatusBadge";
import {
  useListBusinessesBusinessesGet,
  useGetStatsBusinessesStatsGet,
} from "@/api/endpoints/businesses/businesses";
import { useWebSocketStore } from "@/stores/websocket";

type SortField = "name" | "rating" | "lead_score";
type SortDirection = "asc" | "desc";

interface BusinessRow {
  place_id: string;
  name: string;
  status: string;
  city?: string;
  rating?: number;
  lead_score?: number;
}

export default function BusinessTable() {
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortField, setSortField] = useState<SortField>("name");
  const [sortDir, setSortDir] = useState<SortDirection>("asc");
  const navigate = useNavigate();

  const { data: businessesData, refetch } = useListBusinessesBusinessesGet(
    statusFilter !== "all" ? { status: statusFilter } : undefined,
  );
  const { data: statsData } = useGetStatsBusinessesStatsGet();

  const events = useWebSocketStore((s) => s.events);
  const lastStepDone = events.findLast((e) => e.event_type === "step_done");

  useEffect(() => {
    if (lastStepDone) {
      void refetch();
    }
  }, [lastStepDone, refetch]);

  const businesses: BusinessRow[] = useMemo(() => {
    const raw = businessesData?.data ?? [];
    return raw.map((b) => {
      const biz = b as Record<string, unknown>;
      return {
        place_id: biz.place_id as string,
        name: (biz.name as string) ?? "Unknown",
        status: (biz.status as string) ?? "unknown",
        city: biz.city as string | undefined,
        rating: biz.rating as number | undefined,
        lead_score: biz.lead_score as number | undefined,
      };
    });
  }, [businessesData]);

  const sorted = useMemo(() => {
    const items = [...businesses];
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
  }, [businesses, sortField, sortDir]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  };

  const stats = statsData?.data;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 flex-wrap">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            {stats &&
              Object.entries(stats).map(([status, count]) => (
                <SelectItem key={status} value={status}>
                  {status.replace(/_/g, " ")} ({count})
                </SelectItem>
              ))}
          </SelectContent>
        </Select>

        {stats && (
          <div className="flex flex-wrap gap-1">
            {Object.entries(stats).map(([status, count]) => (
              <Badge
                key={status}
                variant="outline"
                className="cursor-pointer"
                onClick={() => setStatusFilter(status)}
              >
                {status.replace(/_/g, " ")}: {count}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {sorted.length === 0 ? (
        <p className="py-8 text-center text-muted-foreground">
          No businesses found
        </p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleSort("name")}
                >
                  Name <ArrowUpDown className="ml-1 h-3 w-3" />
                </Button>
              </TableHead>
              <TableHead>Place ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>City</TableHead>
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
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((biz) => (
              <TableRow
                key={biz.place_id}
                className="cursor-pointer"
                onClick={() => navigate(`/businesses/${biz.place_id}`)}
              >
                <TableCell className="font-medium">{biz.name}</TableCell>
                <TableCell className="font-mono text-xs">
                  {biz.place_id.slice(0, 12)}...
                </TableCell>
                <TableCell>
                  <StatusBadge status={biz.status} />
                </TableCell>
                <TableCell>{biz.city ?? "—"}</TableCell>
                <TableCell>{biz.rating ?? "—"}</TableCell>
                <TableCell>{biz.lead_score ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
