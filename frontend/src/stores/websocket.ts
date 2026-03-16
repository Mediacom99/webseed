import { create } from "zustand";
import type { PipelineEvent } from "@/types";

const MAX_EVENTS = 200;
const MAX_BACKOFF_MS = 30_000;
const WS_BASE_URL = import.meta.env.VITE_WS_URL ?? "/ws";
const STORAGE_KEY = "webseed-ws-events";

interface ActiveJob {
  jobId: string;
  startedAt: string;
  currentStep?: string;
}

interface WebSocketState {
  isConnected: boolean;
  events: PipelineEvent[];
  activeJobs: Map<string, ActiveJob>;

  connect: (apiKey: string) => void;
  disconnect: () => void;
  clearEvents: () => void;
}

let socket: WebSocket | null = null;
let reconnectAttempt = 0;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let shouldReconnect = false;
let currentApiKey: string | null = null;

function getBackoffMs(): number {
  const ms = Math.min(1000 * 2 ** reconnectAttempt, MAX_BACKOFF_MS);
  return ms;
}

function getWsUrl(apiKey: string): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  return `${protocol}//${host}${WS_BASE_URL}?api_key=${encodeURIComponent(apiKey)}`;
}

function persistState(
  events: PipelineEvent[],
  activeJobs: Map<string, ActiveJob>,
) {
  try {
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        events,
        activeJobs: Array.from(activeJobs.entries()),
      }),
    );
  } catch {
    // Ignore quota errors
  }
}

function loadPersistedState(): {
  events: PipelineEvent[];
  activeJobs: Map<string, ActiveJob>;
} {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return { events: [], activeJobs: new Map() };
    const parsed = JSON.parse(raw) as {
      events?: PipelineEvent[];
      activeJobs?: [string, ActiveJob][];
    };
    return {
      events: parsed.events ?? [],
      activeJobs: new Map(parsed.activeJobs ?? []),
    };
  } catch {
    return { events: [], activeJobs: new Map() };
  }
}

const persisted = loadPersistedState();

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  isConnected: false,
  events: persisted.events,
  activeJobs: persisted.activeJobs,

  connect: (apiKey: string) => {
    // Already connected with same key
    if (
      socket &&
      socket.readyState === WebSocket.OPEN &&
      currentApiKey === apiKey
    ) {
      return;
    }

    // Clean up existing connection
    get().disconnect();

    currentApiKey = apiKey;
    shouldReconnect = true;
    reconnectAttempt = 0;

    function doConnect() {
      if (!shouldReconnect || !currentApiKey) return;

      const ws = new WebSocket(getWsUrl(currentApiKey));
      socket = ws;

      ws.onopen = () => {
        // Ignore events from stale sockets (e.g. React Strict Mode double-mount)
        if (ws !== socket) return;
        reconnectAttempt = 0;
        set({ isConnected: true });
      };

      ws.onmessage = (event: MessageEvent) => {
        if (ws !== socket) return;
        try {
          const parsed = JSON.parse(event.data as string) as PipelineEvent;
          const state = get();

          // Update events buffer (cap at MAX_EVENTS)
          const newEvents = [...state.events, parsed];
          if (newEvents.length > MAX_EVENTS) {
            newEvents.splice(0, newEvents.length - MAX_EVENTS);
          }

          // Update active jobs
          const activeJobs = new Map(state.activeJobs);

          if (parsed.event_type === "step_start") {
            activeJobs.set(parsed.job_id, {
              jobId: parsed.job_id,
              startedAt: parsed.timestamp,
              currentStep: parsed.step,
            });
          } else if (parsed.event_type === "job_complete") {
            activeJobs.delete(parsed.job_id);
          }

          persistState(newEvents, activeJobs);
          set({ events: newEvents, activeJobs });
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        if (ws !== socket) return;
        socket = null;
        set({ isConnected: false });

        if (shouldReconnect) {
          const backoff = getBackoffMs();
          reconnectAttempt++;
          reconnectTimer = setTimeout(doConnect, backoff);
        }
      };

      ws.onerror = () => {
        if (ws !== socket) return;
        // onclose will fire after onerror, so reconnect is handled there
      };
    }

    doConnect();
  },

  disconnect: () => {
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

    set({ isConnected: false });
  },

  clearEvents: () => {
    sessionStorage.removeItem(STORAGE_KEY);
    set({ events: [], activeJobs: new Map() });
  },
}));
