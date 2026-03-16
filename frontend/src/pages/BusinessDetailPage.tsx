import { useParams } from "react-router-dom";
import BusinessDetail from "@/components/businesses/BusinessDetail";
import { useGetBusinessBusinessesPlaceIdGet } from "@/api/endpoints/businesses/businesses";

export default function BusinessDetailPage() {
  const { placeId } = useParams<{ placeId: string }>();
  const { data, isLoading, error, refetch } =
    useGetBusinessBusinessesPlaceIdGet(placeId ?? "");

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
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">
        {(business.name as string) ?? "Business Detail"}
      </h1>
      <BusinessDetail
        business={business as never}
        onRefresh={() => void refetch()}
      />
    </div>
  );
}
