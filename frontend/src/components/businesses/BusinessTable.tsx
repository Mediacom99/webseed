import { useState, useMemo, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowUpDown, Trash2, XCircle } from "lucide-react";
import { toast } from "sonner";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import StatusBadge from "@/components/businesses/StatusBadge";
import {
  useListBusinessesBusinessesGet,
  useGetStatsBusinessesStatsGet,
  useHardDeleteBusinessesHardDeletePost,
  useCloseBusinessesBusinessesClosePost,
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
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  const { data: businessesData, refetch } = useListBusinessesBusinessesGet(
    statusFilter !== "all" ? { status: statusFilter } : undefined,
  );
  const { data: statsData } = useGetStatsBusinessesStatsGet();
  const hardDelete = useHardDeleteBusinessesHardDeletePost();
  const closeBiz = useCloseBusinessesBusinessesClosePost();

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

  const toggleSelect = (placeId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(placeId)) next.delete(placeId);
      else next.add(placeId);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === sorted.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(sorted.map((b) => b.place_id)));
    }
  };

  const handleHardDelete = () => {
    hardDelete.mutate(
      { data: { place_ids: Array.from(selectedIds) } },
      {
        onSuccess: () => {
          toast.success(`Deleted ${selectedIds.size} businesses`);
          setSelectedIds(new Set());
          void refetch();
        },
        onError: () => toast.error("Failed to delete businesses"),
      },
    );
  };

  const handleClose = () => {
    closeBiz.mutate(
      { data: { place_ids: Array.from(selectedIds) } },
      {
        onSuccess: () => {
          toast.success(`Closed ${selectedIds.size} businesses`);
          setSelectedIds(new Set());
          void refetch();
        },
        onError: () => toast.error("Failed to close businesses"),
      },
    );
  };

  const handleCsvExport = () => {
    const apiKey = localStorage.getItem("webseed-api-key");
    const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
    const url = `${baseUrl}/businesses/export/csv`;

    const link = document.createElement("a");
    link.href = url;

    // For CSV download, we need to handle the API key
    fetch(url, {
      headers: apiKey ? { "X-API-Key": apiKey } : {},
    })
      .then((r) => r.blob())
      .then((blob) => {
        const blobUrl = URL.createObjectURL(blob);
        link.href = blobUrl;
        link.download = "businesses.csv";
        link.click();
        URL.revokeObjectURL(blobUrl);
      })
      .catch(() => toast.error("Failed to export CSV"));
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

        <Button variant="outline" size="sm" onClick={handleCsvExport}>
          Export CSV
        </Button>

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

      {selectedIds.size > 0 && (
        <div className="flex items-center gap-2 rounded-md border bg-muted p-2">
          <span className="text-sm font-medium">
            {selectedIds.size} selected
          </span>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" size="sm">
                <Trash2 className="mr-1 h-3 w-3" /> Hard Delete
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete {selectedIds.size} businesses?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently remove the selected businesses from the
                  database.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleHardDelete}>
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
          <Button variant="outline" size="sm" onClick={handleClose}>
            <XCircle className="mr-1 h-3 w-3" /> Close
          </Button>
        </div>
      )}

      {sorted.length === 0 ? (
        <p className="py-8 text-center text-muted-foreground">
          No businesses found
        </p>
      ) : (
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
                data-selected={selectedIds.has(biz.place_id)}
              >
                <TableCell onClick={(e) => e.stopPropagation()}>
                  <Checkbox
                    checked={selectedIds.has(biz.place_id)}
                    onCheckedChange={() => toggleSelect(biz.place_id)}
                    aria-label={`Select ${biz.name}`}
                  />
                </TableCell>
                <TableCell
                  className="font-medium"
                  onClick={() => navigate(`/businesses/${biz.place_id}`)}
                >
                  {biz.name}
                </TableCell>
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
