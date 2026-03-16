import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/stores/auth";
import { customFetch, ApiError } from "@/api/client";

export default function LoginPage() {
  const [key, setKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const setApiKey = useAuthStore((s) => s.setApiKey);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!key.trim()) return;

    setLoading(true);
    setError(null);

    // Temporarily store the key so customFetch can use it
    localStorage.setItem("webseed-api-key", key.trim());

    try {
      await customFetch("/businesses/stats", { method: "GET" });
      setApiKey(key.trim());
      toast.success("Authenticated successfully");
      navigate("/", { replace: true });
    } catch (err) {
      localStorage.removeItem("webseed-api-key");
      if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
        setError("Invalid API key");
      } else {
        setError(err instanceof Error ? err.message : "Connection failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>webseed</CardTitle>
          <CardDescription>Enter your API key to continue</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="api-key">API Key</Label>
              <Input
                id="api-key"
                type="password"
                placeholder="Enter your API key"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                autoFocus
              />
            </div>

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}

            <Button type="submit" className="w-full" disabled={loading || !key.trim()}>
              {loading ? "Validating..." : "Sign in"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
