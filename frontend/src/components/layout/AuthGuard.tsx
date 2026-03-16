import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/stores/auth";

export default function AuthGuard() {
  const apiKey = useAuthStore((s) => s.apiKey);

  if (!apiKey) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
