import { useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/stores/auth";
import { useWebSocketStore } from "@/stores/websocket";

export default function AuthGuard() {
  const apiKey = useAuthStore((s) => s.apiKey);
  const connect = useWebSocketStore((s) => s.connect);
  const disconnect = useWebSocketStore((s) => s.disconnect);

  useEffect(() => {
    if (apiKey) {
      connect(apiKey);
    }
    return () => {
      disconnect();
    };
  }, [apiKey, connect, disconnect]);

  if (!apiKey) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
