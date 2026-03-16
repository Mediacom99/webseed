import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronUp, ChevronDown, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useWebSocketStore } from "@/stores/websocket";
import type { PipelineEvent } from "@/types";

const MIN_HEIGHT = 120;
const MAX_HEIGHT = 500;
const DEFAULT_HEIGHT = 250;

const EVENT_COLORS: Record<string, string> = {
  step_start: "text-blue-600 dark:text-blue-400",
  step_done: "text-green-600 dark:text-green-400",
  step_error: "text-red-600 dark:text-red-400",
  cost: "text-amber-600 dark:text-amber-400",
  progress: "text-muted-foreground",
  job_complete: "text-green-600 dark:text-green-400",
};

function formatTime(timestamp: string): string {
  try {
    const d = new Date(timestamp);
    return d.toLocaleTimeString("it-IT", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return timestamp;
  }
}

function EventRow({ event }: { event: PipelineEvent }) {
  const colorClass = EVENT_COLORS[event.event_type] ?? "text-muted-foreground";
  return (
    <div className="flex gap-3 px-3 py-1 text-xs font-mono hover:bg-muted/50">
      <span className="shrink-0 text-muted-foreground">
        {formatTime(event.timestamp)}
      </span>
      <span className={cn("shrink-0 w-20", colorClass)}>
        {event.event_type}
      </span>
      <span className="shrink-0 w-16 text-muted-foreground">{event.step}</span>
      <span className="truncate">{event.message}</span>
    </div>
  );
}

export default function BottomPanel() {
  const [expanded, setExpanded] = useState(false);
  const [panelHeight, setPanelHeight] = useState(DEFAULT_HEIGHT);
  const [userScrolled, setUserScrolled] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);
  const resizingRef = useRef(false);
  const startYRef = useRef(0);
  const startHeightRef = useRef(0);

  const isConnected = useWebSocketStore((s) => s.isConnected);
  const events = useWebSocketStore((s) => s.events);
  const activeJobs = useWebSocketStore((s) => s.activeJobs);
  const clearEvents = useWebSocketStore((s) => s.clearEvents);

  const lastEvent = events.length > 0 ? events[events.length - 1] : null;
  const jobCount = activeJobs.size;

  // Auto-scroll to bottom when new events arrive (unless user scrolled up)
  useEffect(() => {
    if (!userScrolled && logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [events, userScrolled]);

  const handleScroll = useCallback(() => {
    if (!logRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = logRef.current;
    // If user scrolled up more than 40px from bottom, pause auto-scroll
    const atBottom = scrollHeight - scrollTop - clientHeight < 40;
    setUserScrolled(!atBottom);
  }, []);

  // Resize handle
  const handleResizeStart = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      e.preventDefault();
      resizingRef.current = true;
      startYRef.current =
        "touches" in e ? e.touches[0].clientY : e.clientY;
      startHeightRef.current = panelHeight;

      const handleMove = (ev: MouseEvent | TouchEvent) => {
        if (!resizingRef.current) return;
        const currentY =
          "touches" in ev
            ? (ev as TouchEvent).touches[0].clientY
            : (ev as MouseEvent).clientY;
        const delta = startYRef.current - currentY;
        const newHeight = Math.min(
          MAX_HEIGHT,
          Math.max(MIN_HEIGHT, startHeightRef.current + delta),
        );
        setPanelHeight(newHeight);
      };

      const handleEnd = () => {
        resizingRef.current = false;
        document.removeEventListener("mousemove", handleMove);
        document.removeEventListener("mouseup", handleEnd);
        document.removeEventListener("touchmove", handleMove);
        document.removeEventListener("touchend", handleEnd);
      };

      document.addEventListener("mousemove", handleMove);
      document.addEventListener("mouseup", handleEnd);
      document.addEventListener("touchmove", handleMove);
      document.addEventListener("touchend", handleEnd);
    },
    [panelHeight],
  );

  return (
    <div
      className="border-t bg-background"
      style={{ height: expanded ? panelHeight + 32 : 32 }}
    >
      {/* Resize handle (only when expanded) */}
      {expanded && (
        <div
          className="flex h-2 cursor-row-resize items-center justify-center hover:bg-muted"
          onMouseDown={handleResizeStart}
          onTouchStart={handleResizeStart}
          role="separator"
          aria-orientation="horizontal"
          aria-label="Resize panel"
        >
          <div className="h-0.5 w-8 rounded-full bg-border" />
        </div>
      )}

      {/* Collapsed bar */}
      <button
        type="button"
        className="flex h-8 w-full items-center gap-3 px-3 text-xs hover:bg-muted/50"
        onClick={() => setExpanded(!expanded)}
        aria-label={expanded ? "Collapse event panel" : "Expand event panel"}
        aria-expanded={expanded}
      >
        {/* Connection dot */}
        <span
          className={cn(
            "h-2 w-2 shrink-0 rounded-full",
            isConnected ? "bg-green-500" : "bg-red-500",
          )}
          aria-label={isConnected ? "Connected" : "Disconnected"}
        />

        {/* Job status */}
        <span className="shrink-0 text-muted-foreground">
          {jobCount > 0
            ? `${jobCount} job${jobCount > 1 ? "s" : ""} running`
            : "Idle"}
        </span>

        {/* Last event */}
        {lastEvent && (
          <span className="truncate text-muted-foreground">
            {lastEvent.message}
          </span>
        )}

        <span className="ml-auto shrink-0">
          {expanded ? (
            <ChevronDown className="h-3 w-3" />
          ) : (
            <ChevronUp className="h-3 w-3" />
          )}
        </span>
      </button>

      {/* Expanded event log */}
      {expanded && (
        <div className="flex flex-col" style={{ height: panelHeight - 8 }}>
          {/* Toolbar */}
          <div className="flex items-center justify-between border-b px-3 py-1">
            <span className="text-xs font-medium text-muted-foreground">
              Events ({events.length})
            </span>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 gap-1 px-2 text-xs"
              onClick={clearEvents}
              aria-label="Clear events"
            >
              <Trash2 className="h-3 w-3" />
              Clear
            </Button>
          </div>

          {/* Event log */}
          <div
            ref={logRef}
            className="flex-1 overflow-auto"
            onScroll={handleScroll}
          >
            {events.length === 0 ? (
              <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                No events yet
              </div>
            ) : (
              events.map((event, i) => <EventRow key={i} event={event} />)
            )}
          </div>
        </div>
      )}
    </div>
  );
}
