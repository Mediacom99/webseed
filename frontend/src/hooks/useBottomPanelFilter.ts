import { useMemo } from "react";
import { useLocation, useParams } from "react-router-dom";
import { useWebSocketStore } from "@/stores/websocket";
import type { PipelineEvent } from "@/types";

export type TabId = "all" | `job:${string}` | "this-business";

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

  // "This Business" tab only on detail page
  const isDetailPage = location.pathname.startsWith("/businesses/") && params.placeId;
  const placeId = params.placeId;

  const tabs = useMemo<PanelTab[]>(() => {
    const result: PanelTab[] = [{ id: "all", label: "All", status: null }];
    result.push(...jobTabs);
    if (isDetailPage) {
      result.push({ id: "this-business", label: "This Business", status: null });
    }
    return result;
  }, [jobTabs, isDetailPage]);

  // Auto-selected tab based on route
  const autoTab = useMemo<TabId>(() => {
    if (isDetailPage) return "this-business";
    if (location.pathname === "/search" && jobTabs.length > 0) {
      // Most recent search job = last job tab
      return jobTabs[jobTabs.length - 1].id;
    }
    return "all";
  }, [location.pathname, isDetailPage, jobTabs]);

  // Filter function
  function filterEvents(selectedTab: TabId): PipelineEvent[] {
    if (selectedTab === "all") return events;
    if (selectedTab === "this-business" && placeId) {
      return events.filter((e) => e.place_id === placeId);
    }
    if (selectedTab.startsWith("job:")) {
      const jobId = selectedTab.slice(4);
      return events.filter((e) => e.job_id === jobId);
    }
    return events;
  }

  return { tabs, autoTab, filterEvents };
}
