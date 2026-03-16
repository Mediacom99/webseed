import StatsCards from "@/components/dashboard/StatsCards";
import ActiveJobs from "@/components/dashboard/ActiveJobs";
import RecentActivity from "@/components/dashboard/RecentActivity";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <StatsCards />
      <div className="grid gap-6 md:grid-cols-2">
        <ActiveJobs />
        <RecentActivity />
      </div>
    </div>
  );
}
