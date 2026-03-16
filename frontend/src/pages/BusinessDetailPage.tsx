import { useEffect } from "react";
import { useParams } from "react-router-dom";
import BusinessDetail from "@/components/businesses/BusinessDetail";
import { useGetBusinessBusinessesPlaceIdGet } from "@/api/endpoints/businesses/businesses";
import { useWebSocketStore } from "@/stores/websocket";

export default function BusinessDetailPage() {
  const { placeId } = useParams<{ placeId: string }>();
  const { data, isLoading, error, refetch } =
    useGetBusinessBusinessesPlaceIdGet(placeId ?? "");

  const events = useWebSocketStore((s) => s.events);

  // Refetch when WS events arrive for this business
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
    return <p className="text-muted-foreground">Loading...</p>;
  }

  if (error || !data?.data) {
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
