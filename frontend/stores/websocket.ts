import { defineStore } from "pinia";
import type { PipelineEvent, ActiveJob } from "~/types";

const MAX_EVENTS = 200;
const MAX_BACKOFF_MS = 30_000;
const MAX_RECONNECT_ATTEMPTS = 15;
const STORAGE_KEY = "webseed-ws-events";

let socket: WebSocket | null = null;
let reconnectAttempt = 0;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let shouldReconnect = false;
let currentApiKey: string | null = null;

function getBackoffMs(): number {
  return Math.min(1000 * 2 ** reconnectAttempt, MAX_BACKOFF_MS);
}

function buildWsUrl(apiKey: string, wsBase: string): string {
  // If wsBase is already a full URL (ws:// or wss://), use it directly
  if (wsBase.startsWith("ws://") || wsBase.startsWith("wss://")) {
    return `${wsBase}?api_key=${encodeURIComponent(apiKey)}`;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  return `${protocol}//${host}${wsBase}?api_key=${encodeURIComponent(apiKey)}`;
}

interface PersistedState {
  events?: PipelineEvent[];
  activeJobs?: [string, ActiveJob][];
}

function persistState(
  events: PipelineEvent[],
  activeJobs: Record<string, ActiveJob>,
): void {
  try {
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        events,
        activeJobs: Object.entries(activeJobs),
      }),
    );
  } catch {
    // Ignore quota errors
  }
}

function loadPersistedState(): {
  events: PipelineEvent[];
  activeJobs: Record<string, ActiveJob>;
} {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return { events: [], activeJobs: {} };
    const parsed = JSON.parse(raw) as PersistedState;
    return {
      events: parsed.events ?? [],
      activeJobs: Object.fromEntries(parsed.activeJobs ?? []),
    };
  } catch {
    return { events: [], activeJobs: {} };
  }
}

export const useWebSocketStore = defineStore("websocket", {
  state: () => {
    const persisted = loadPersistedState();
    return {
      isConnected: false,
      events: persisted.events as PipelineEvent[],
      activeJobs: persisted.activeJobs as Record<string, ActiveJob>,
    };
  },

  getters: {
    activeJobCount: (state) => Object.keys(state.activeJobs).length,

    lastEvent: (state) =>
      state.events.length > 0
        ? state.events[state.events.length - 1]
        : null,
  },

  actions: {
    connect(apiKey: string, wsBase: string) {
      if (
        socket &&
        socket.readyState === WebSocket.OPEN &&
        currentApiKey === apiKey
      ) {
        return;
      }

      this.disconnect();
      currentApiKey = apiKey;
      shouldReconnect = true;
      reconnectAttempt = 0;

      const doConnect = () => {
        if (!shouldReconnect || !currentApiKey) return;

        const ws = new WebSocket(buildWsUrl(currentApiKey, wsBase));
        socket = ws;

        ws.onopen = () => {
          if (ws !== socket) return;
          reconnectAttempt = 0;
          this.isConnected = true;
        };

        ws.onmessage = (event: MessageEvent) => {
          if (ws !== socket) return;
          try {
            const parsed = JSON.parse(event.data as string) as PipelineEvent;

            const newEvents = [...this.events, parsed];
            if (newEvents.length > MAX_EVENTS) {
              newEvents.splice(0, newEvents.length - MAX_EVENTS);
            }

            const activeJobs = { ...this.activeJobs };
            if (parsed.event_type === "step_start") {
              activeJobs[parsed.job_id] = {
                jobId: parsed.job_id,
                startedAt: parsed.timestamp,
                currentStep: parsed.step,
              };
            } else if (
              parsed.event_type === "job_complete" ||
              parsed.event_type === "step_error"
            ) {
              delete activeJobs[parsed.job_id];
            }

            persistState(newEvents, activeJobs);
            this.events = newEvents;
            this.activeJobs = activeJobs;
          } catch {
            // Ignore malformed messages
          }
        };

        ws.onclose = (event: CloseEvent) => {
          if (ws !== socket) return;
          socket = null;
          this.isConnected = false;

          // Don't reconnect on auth failure (backend sends 4001)
          if (event.code === 4001) {
            shouldReconnect = false;
            return;
          }

          if (shouldReconnect && reconnectAttempt < MAX_RECONNECT_ATTEMPTS) {
            const backoff = getBackoffMs();
            reconnectAttempt++;
            reconnectTimer = setTimeout(doConnect, backoff);
          }
        };

        ws.onerror = () => {
          if (ws !== socket) return;
          // onclose will fire after onerror
        };
      };

      doConnect();
    },

    disconnect() {
      shouldReconnect = false;
      currentApiKey = null;

      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }

      if (socket) {
        socket.close();
        socket = null;
      }

      this.isConnected = false;
    },

    clearEvents() {
      sessionStorage.removeItem(STORAGE_KEY);
      this.$patch({ events: [], activeJobs: {} });
    },
  },
});
