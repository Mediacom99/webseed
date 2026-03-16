import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useWebSocketStore } from "@/stores/websocket";
import { cn } from "@/lib/utils";
import type { EventType } from "@/types";

const EVENT_COLORS: Record<EventType, string> = {
  step_start: "text-blue-600",
  step_done: "text-green-600",
  step_error: "text-red-600",
  progress: "text-muted-foreground",
  cost: "text-muted-foreground",
  job_complete: "text-green-700 font-medium",
};

export default function RecentActivity() {
  const events = useWebSocketStore((s) => s.events);
  const recent = events.slice(-50);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        {recent.length === 0 ? (
          <p className="text-sm text-muted-foreground">No recent activity</p>
        ) : (
          <ScrollArea className="h-64">
            <div className="space-y-1">
              {recent.map((event, i) => (
                <div
                  key={`${event.job_id}-${event.timestamp}-${i}`}
                  className="flex items-start gap-2 text-sm"
                >
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </span>
                  <span
                    className={cn(
                      "truncate",
                      EVENT_COLORS[event.event_type] ?? "text-foreground",
                    )}
                  >
                    [{event.step}] {event.message}
                  </span>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
