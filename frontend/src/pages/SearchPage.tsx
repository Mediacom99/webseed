import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import SearchForm from "@/components/search/SearchForm";
import SearchResultsTable, {
  type SearchResult,
} from "@/components/search/SearchResultsTable";
import SearchActionBar from "@/components/search/SearchActionBar";
import { useListBusinessesBusinessesGet } from "@/api/endpoints/businesses/businesses";
import { useWebSocketStore } from "@/stores/websocket";

export default function SearchPage() {
  const [lastJobId, setLastJobId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const { data, refetch } = useListBusinessesBusinessesGet(
    { status: "searched" },
    { query: { enabled: true } },
  );

  const events = useWebSocketStore((s) => s.events);

  // Refetch when search step_done event for our job arrives
  const lastSearchDone = events.findLast(
    (e) =>
      e.event_type === "step_done" &&
      e.step === "search" &&
      (lastJobId === null || e.job_id === lastJobId),
  );
  useEffect(() => {
    if (lastSearchDone) {
      void refetch();
    }
  }, [lastSearchDone, refetch]);

  const results: SearchResult[] = useMemo(() => {
    if (!data?.data) return [];
    const items = data.data as Array<Record<string, unknown>>;
    return items.map((b) => ({
      place_id: (b.place_id as string) ?? "",
      name: (b.name as string) ?? "",
      category: (b.category as string) ?? "",
      rating: (b.rating as number) ?? 0,
      reviews: (b.reviews as number) ?? 0,
      address: (b.address as string) ?? "",
      lead_score: (b.lead_score as number) ?? 0,
    }));
  }, [data]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Search</h1>
      <Card>
        <CardHeader>
          <CardTitle>Find Businesses</CardTitle>
        </CardHeader>
        <CardContent>
          <SearchForm onJobStarted={setLastJobId} />
        </CardContent>
      </Card>

      {lastJobId && results.length === 0 && (
        <p className="py-8 text-center text-muted-foreground">
          No results
        </p>
      )}

      {results.length > 0 && (
        <>
          <div className="space-y-2">
            <h2 className="text-lg font-medium">
              Results ({results.length})
            </h2>
            <SearchResultsTable
              results={results}
              selected={selected}
              onSelectionChange={setSelected}
            />
          </div>
          <SearchActionBar
            selectedIds={selected}
            onActionComplete={() => {
              setSelected(new Set());
              void refetch();
            }}
          />
        </>
      )}
    </div>
  );
}
