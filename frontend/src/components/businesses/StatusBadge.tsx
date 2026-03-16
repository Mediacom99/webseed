import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const STATUS_COLORS: Record<string, string> = {
  searched: "bg-blue-100 text-blue-800",
  enriched: "bg-purple-100 text-purple-800",
  generated: "bg-green-100 text-green-800",
  tested: "bg-teal-100 text-teal-800",
  deployed: "bg-emerald-100 text-emerald-800",
  email_queued: "bg-amber-100 text-amber-800",
  emailed: "bg-indigo-100 text-indigo-800",
  running_enrich: "bg-blue-100 text-blue-800 animate-pulse",
  running_generate: "bg-blue-100 text-blue-800 animate-pulse",
  running_test: "bg-blue-100 text-blue-800 animate-pulse",
  running_deploy: "bg-blue-100 text-blue-800 animate-pulse",
  running_email: "bg-blue-100 text-blue-800 animate-pulse",
  error_enrich: "bg-red-100 text-red-800",
  error_generate: "bg-red-100 text-red-800",
  error_test: "bg-red-100 text-red-800",
  error_deploy: "bg-red-100 text-red-800",
  error_email: "bg-red-100 text-red-800",
  error_run: "bg-red-100 text-red-800",
  opted_out: "bg-gray-100 text-gray-800",
};

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <Badge
      variant="secondary"
      className={cn(STATUS_COLORS[status] ?? "")}
    >
      {status.replace(/_/g, " ")}
    </Badge>
  );
}
