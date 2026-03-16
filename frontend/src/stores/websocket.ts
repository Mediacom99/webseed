import { create } from "zustand";
import type { PipelineEvent } from "@/types";

const MAX_EVENTS = 200;
const MAX_BACKOFF_MS = 30_000;
const WS_BASE_URL = import.meta.env.VITE_WS_URL ?? "/ws";

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

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  isConnected: false,
  events: [],
  activeJobs: new Map(),

  connect: (apiKey: string) => {
    // Already connected with same key
    if (socket && socket.readyState === WebSocket.OPEN && currentApiKey === apiKey) {
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
        reconnectAttempt = 0;
        set({ isConnected: true });
      };

      ws.onmessage = (event: MessageEvent) => {
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
          } else if (
            parsed.event_type === "job_complete" ||
            parsed.event_type === "step_error"
          ) {
            // Only remove on job_complete, not individual step errors
            if (parsed.event_type === "job_complete") {
              activeJobs.delete(parsed.job_id);
            }
          }

          // Update current step for running jobs
          if (
            parsed.event_type === "step_start" &&
            activeJobs.has(parsed.job_id)
          ) {
            const job = activeJobs.get(parsed.job_id)!;
            activeJobs.set(parsed.job_id, {
              ...job,
              currentStep: parsed.step,
            });
          }

          set({ events: newEvents, activeJobs });
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        socket = null;
        set({ isConnected: false });

        if (shouldReconnect) {
          const backoff = getBackoffMs();
          reconnectAttempt++;
          reconnectTimer = setTimeout(doConnect, backoff);
        }
      };

      ws.onerror = () => {
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
    set({ events: [], activeJobs: new Map() });
  },
}));
