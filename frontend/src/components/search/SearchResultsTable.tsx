import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export interface SearchResult {
  place_id: string;
  name: string;
  category: string;
  rating: number;
  reviews: number;
  address: string;
  lead_score: number;
}

type SortKey = "rating" | "reviews" | "lead_score";
type SortDir = "asc" | "desc";

interface SearchResultsTableProps {
  results: SearchResult[];
  selected: Set<string>;
  onSelectionChange: (selected: Set<string>) => void;
}

export default function SearchResultsTable({
  results,
  selected,
  onSelectionChange,
}: SearchResultsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("lead_score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const sorted = [...results].sort((a, b) => {
    const mul = sortDir === "asc" ? 1 : -1;
    return (a[sortKey] - b[sortKey]) * mul;
  });

  const allSelected = results.length > 0 && selected.size === results.length;

  const toggleAll = () => {
    if (allSelected) {
      onSelectionChange(new Set());
    } else {
      onSelectionChange(new Set(results.map((r) => r.place_id)));
    }
  };

  const toggleOne = (placeId: string) => {
    const next = new Set(selected);
    if (next.has(placeId)) {
      next.delete(placeId);
    } else {
      next.add(placeId);
    }
    onSelectionChange(next);
  };

  const sortIndicator = (key: SortKey) => {
    if (sortKey !== key) return "";
    return sortDir === "asc" ? " \u2191" : " \u2193";
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">
              <Checkbox
                checked={allSelected}
                onCheckedChange={toggleAll}
                aria-label="Select all"
              />
            </TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Category</TableHead>
            <TableHead
              className="cursor-pointer select-none"
              onClick={() => toggleSort("rating")}
            >
              Rating{sortIndicator("rating")}
            </TableHead>
            <TableHead
              className="cursor-pointer select-none"
              onClick={() => toggleSort("reviews")}
            >
              Reviews{sortIndicator("reviews")}
            </TableHead>
            <TableHead>Address</TableHead>
            <TableHead
              className="cursor-pointer select-none"
              onClick={() => toggleSort("lead_score")}
            >
              Pre-score{sortIndicator("lead_score")}
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((r) => (
            <TableRow key={r.place_id}>
              <TableCell>
                <Checkbox
                  checked={selected.has(r.place_id)}
                  onCheckedChange={() => toggleOne(r.place_id)}
                  aria-label={`Select ${r.name}`}
                />
              </TableCell>
              <TableCell className="font-medium">{r.name}</TableCell>
              <TableCell className="capitalize">
                {r.category.replace(/_/g, " ")}
              </TableCell>
              <TableCell>{r.rating.toFixed(1)}</TableCell>
              <TableCell>{r.reviews}</TableCell>
              <TableCell className="max-w-[200px] truncate">
                {r.address}
              </TableCell>
              <TableCell>{r.lead_score}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
