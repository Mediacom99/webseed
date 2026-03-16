import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import BusinessDetail from "@/components/businesses/BusinessDetail";
import BusinessDetailSkeleton from "@/components/businesses/BusinessDetailSkeleton";
import { useGetBusinessBusinessesPlaceIdGet } from "@/api/endpoints/businesses/businesses";
import { useWebSocketStore } from "@/stores/websocket";

export default function BusinessDetailPage() {
  const { placeId } = useParams<{ placeId: string }>();
  const { data, isLoading, error, refetch } =
    useGetBusinessBusinessesPlaceIdGet(placeId ?? "");

  const events = useWebSocketStore((s) => s.events);

  const lastRelevantEvent = events.findLast(
    (e) =>
      (e.event_type === "step_done" || e.event_type === "step_error") &&
      e.place_id === placeId,
  );
  useEffect(() => {
    if (lastRelevantEvent) {
      void refetch();
    }
  }, [lastRelevantEvent, refetch]);

  if (isLoading) {
    return <BusinessDetailSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <AlertCircle className="mb-4 h-10 w-10 text-destructive" />
        <h2 className="text-lg font-semibold">Failed to load business</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          {error instanceof Error ? error.message : "Unknown error"}
        </p>
        <Button onClick={() => void refetch()}>Retry</Button>
      </div>
    );
  }

  if (!data?.data) {
    return (
      <div className="py-8 text-center">
        <h2 className="text-lg font-semibold">Business not found</h2>
        <p className="text-muted-foreground">
          No business with place ID: {placeId}
        </p>
      </div>
    );
  }

  const business = data.data as Record<string, unknown>;

  return (
    <BusinessDetail
      business={business as never}
      onRefresh={() => void refetch()}
    />
  );
}
