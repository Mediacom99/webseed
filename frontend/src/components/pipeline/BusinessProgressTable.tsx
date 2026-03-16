import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import StatusBadge from "@/components/businesses/StatusBadge";
import { useWebSocketEvents } from "@/hooks/useWebSocketEvents";

interface BusinessProgress {
  placeId: string;
  name?: string;
  currentStep: string;
  status: string;
}

interface BusinessProgressTableProps {
  jobId: string | null;
}

export default function BusinessProgressTable({
  jobId,
}: BusinessProgressTableProps) {
  const events = useWebSocketEvents(jobId ? { jobId } : undefined);

  // Derive per-business progress from events
  const businesses = new Map<string, BusinessProgress>();

  for (const event of events) {
    if (!event.place_id) continue;

    const existing = businesses.get(event.place_id);
    const name =
      (event.data?.name as string | undefined) ?? existing?.name ?? undefined;

    let status = existing?.status ?? "unknown";
    if (event.event_type === "step_start") {
      status = `running_${event.step}`;
    } else if (event.event_type === "step_done") {
      status = event.step === "search" ? "searched" : event.step;
    } else if (event.event_type === "step_error") {
      status = `error_${event.step}`;
    }

    businesses.set(event.place_id, {
      placeId: event.place_id,
      name,
      currentStep: event.step,
      status,
    });
  }

  const rows = Array.from(businesses.values());

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Business Progress</CardTitle>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No businesses in this job
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Place ID</TableHead>
                <TableHead>Step</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((biz) => (
                <TableRow key={biz.placeId}>
                  <TableCell>{biz.name ?? "—"}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {biz.placeId.slice(0, 12)}...
                  </TableCell>
                  <TableCell className="capitalize">{biz.currentStep}</TableCell>
                  <TableCell>
                    <StatusBadge status={biz.status} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
