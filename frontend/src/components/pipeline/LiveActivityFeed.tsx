import { useEffect, useRef } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useWebSocketEvents } from "@/hooks/useWebSocketEvents";
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

interface LiveActivityFeedProps {
  jobId: string | null;
}

export default function LiveActivityFeed({ jobId }: LiveActivityFeedProps) {
  const events = useWebSocketEvents(jobId ? { jobId } : undefined);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Activity Feed</CardTitle>
      </CardHeader>
      <CardContent>
        {events.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No events yet. Start a job to see activity.
          </p>
        ) : (
          <ScrollArea className="h-48">
            <div className="space-y-1 pr-4">
              {events.map((event, i) => (
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
              <div ref={bottomRef} />
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
