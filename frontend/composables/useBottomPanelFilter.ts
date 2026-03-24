import type { PipelineEvent, TabId } from "~/types";

export interface PanelTab {
  id: TabId;
  label: string;
  status: "running" | "complete" | "error" | null;
}

export function useBottomPanelFilter() {
  const route = useRoute();
  const ws = useWebSocketStore();

  const jobTabs = computed<PanelTab[]>(() => {
    const jobIds = new Set<string>();
    const jobStatus = new Map<string, "running" | "complete" | "error">();

    for (const e of ws.events) {
      jobIds.add(e.job_id);
      if (e.event_type === "job_complete") {
        jobStatus.set(e.job_id, "complete");
      } else if (e.event_type === "step_error") {
        if (jobStatus.get(e.job_id) !== "complete") {
          jobStatus.set(e.job_id, "error");
        }
      }
    }

    for (const jobId of Object.keys(ws.activeJobs)) {
      jobStatus.set(jobId, "running");
    }

    return Array.from(jobIds).map((id) => ({
      id: `job:${id}` as TabId,
      label: id.slice(0, 8),
      status: jobStatus.get(id) ?? null,
    }));
  });

  const tabs = computed<PanelTab[]>(() => [
    { id: "all", label: "All", status: null },
    ...jobTabs.value,
  ]);

  const autoTab = computed<TabId>(() => {
    const path = route.path;
    const placeId = route.params.placeId as string | undefined;

    if (path.startsWith("/businesses/") && placeId) {
      for (let i = ws.events.length - 1; i >= 0; i--) {
        if (ws.events[i].place_id === placeId) {
          return `job:${ws.events[i].job_id}`;
        }
      }
    }

    if (path === "/search" && jobTabs.value.length > 0) {
      return jobTabs.value[jobTabs.value.length - 1].id;
    }

    return "all";
  });

  function filterEvents(selectedTab: TabId): PipelineEvent[] {
    if (selectedTab === "all") return ws.events;
    if (selectedTab.startsWith("job:")) {
      const jobId = selectedTab.slice(4);
      return ws.events.filter((e) => e.job_id === jobId);
    }
    return ws.events;
  }

  return { tabs, autoTab, filterEvents };
}
