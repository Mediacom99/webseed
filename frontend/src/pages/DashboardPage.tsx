import { useNavigate } from "react-router-dom";
import { Search, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import PipelineFunnel from "@/components/dashboard/PipelineFunnel";
import SummaryRow from "@/components/dashboard/SummaryRow";
import ActiveJobs from "@/components/dashboard/ActiveJobs";
import StatsCards from "@/components/dashboard/StatsCards";

export default function DashboardPage() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      <PipelineFunnel />

      <div className="flex flex-wrap items-center justify-between gap-4">
        <SummaryRow />
        <div className="flex gap-2">
          <Button size="sm" onClick={() => void navigate("/search")}>
            <Search className="mr-1.5 h-4 w-4" />
            New Search
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => void navigate("/businesses?status=errors")}
          >
            <AlertCircle className="mr-1.5 h-4 w-4" />
            View Errors
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <ActiveJobs />
        <StatsCards />
      </div>
    </div>
  );
}
