import { useMemo } from "react";
import { useLocation, useParams } from "react-router-dom";
import { useWebSocketStore } from "@/stores/websocket";
import type { PipelineEvent } from "@/types";

export type TabId = "all" | `job:${string}`;

export interface PanelTab {
  id: TabId;
  label: string;
  status: "running" | "complete" | "error" | null;
}

export function useBottomPanelFilter() {
  const location = useLocation();
  const params = useParams<{ placeId: string }>();
  const events = useWebSocketStore((s) => s.events);
  const activeJobs = useWebSocketStore((s) => s.activeJobs);

  // Build tabs from distinct job IDs in events
  const jobTabs = useMemo<PanelTab[]>(() => {
    const jobIds = new Set<string>();
    const jobStatus = new Map<string, "running" | "complete" | "error">();

    for (const e of events) {
      jobIds.add(e.job_id);
      if (e.event_type === "job_complete") {
        jobStatus.set(e.job_id, "complete");
      } else if (e.event_type === "step_error") {
        if (jobStatus.get(e.job_id) !== "complete") {
          jobStatus.set(e.job_id, "error");
        }
      }
    }

    // Mark active jobs as running
    for (const [jobId] of activeJobs) {
      jobStatus.set(jobId, "running");
    }

    return Array.from(jobIds).map((id) => ({
      id: `job:${id}` as TabId,
      label: id.slice(0, 8),
      status: jobStatus.get(id) ?? null,
    }));
  }, [events, activeJobs]);

  const isDetailPage =
    location.pathname.startsWith("/businesses/") && !!params.placeId;
  const placeId = params.placeId;

  const tabs = useMemo<PanelTab[]>(() => {
    const result: PanelTab[] = [{ id: "all", label: "All", status: null }];
    result.push(...jobTabs);
    return result;
  }, [jobTabs]);

  // Auto-selected tab based on route
  // On business detail page: switch to the most recent job tab that has events for this business
  const autoTab = useMemo<TabId>(() => {
    if (isDetailPage && placeId) {
      // Find the most recent job that has events for this business
      for (let i = events.length - 1; i >= 0; i--) {
        if (events[i].place_id === placeId) {
          return `job:${events[i].job_id}`;
        }
      }
    }
    if (location.pathname === "/search" && jobTabs.length > 0) {
      // Most recent search job = last job tab
      return jobTabs[jobTabs.length - 1].id;
    }
    return "all";
  }, [location.pathname, isDetailPage, placeId, events, jobTabs]);

  // Filter function
  function filterEvents(selectedTab: TabId): PipelineEvent[] {
    if (selectedTab === "all") return events;
    if (selectedTab.startsWith("job:")) {
      const jobId = selectedTab.slice(4);
      return events.filter((e) => e.job_id === jobId);
    }
    return events;
  }

  return { tabs, autoTab, filterEvents };
}
