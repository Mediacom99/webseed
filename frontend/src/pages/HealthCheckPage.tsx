import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { customFetch } from "@/api/client";

export default function HealthCheckPage() {
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await customFetch<Record<string, number>>(
        "/businesses/stats",
        { method: "GET" },
      );
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchStats();
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>webseed — Health Check</CardTitle>
          <CardDescription>
            API connectivity test via GET /api/businesses/stats
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading && (
            <p className="text-muted-foreground">Loading...</p>
          )}

          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-destructive text-sm">
              <p className="font-medium">Connection Error</p>
              <p>{error}</p>
            </div>
          )}

          {stats && (
            <pre className="overflow-auto rounded-md bg-muted p-3 text-sm">
              {JSON.stringify(stats, null, 2)}
            </pre>
          )}

          <Button onClick={() => void fetchStats()} disabled={loading}>
            {loading ? "Fetching..." : "Refresh"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
