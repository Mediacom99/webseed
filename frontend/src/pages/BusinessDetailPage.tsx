import { useParams } from "react-router-dom";

export default function BusinessDetailPage() {
  const { placeId } = useParams<{ placeId: string }>();

  return (
    <div>
      <h1 className="text-2xl font-semibold">Business Detail</h1>
      <p className="text-muted-foreground">{placeId}</p>
    </div>
  );
}
