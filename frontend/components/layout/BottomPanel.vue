<script setup lang="ts">
import { ChevronUp, ChevronDown, Trash2 } from "lucide-vue-next";
import { formatTime } from "~/utils/formatters";
import type { TabId, PipelineEvent } from "~/types";

const MIN_HEIGHT = 120;
const MAX_HEIGHT = 500;
const DEFAULT_HEIGHT = 250;

const STATUS_ICONS: Record<string, string> = {
  running: "\u25CF",
  complete: "\u2713",
  error: "\u2717",
};

const STATUS_COLORS: Record<string, string> = {
  running: "text-info",
  complete: "text-success",
  error: "text-error",
};

const EVENT_CLASSES: Record<string, string> = {
  step_start: "text-info",
  step_done: "text-success",
  step_error: "text-error",
  cost: "text-warning",
  progress: "text-base-content/60",
  job_complete: "text-success",
};

const ws = useWebSocketStore();
const { tabs, autoTab, filterEvents } = useBottomPanelFilter();

const expanded = ref(false);
const panelHeight = ref(DEFAULT_HEIGHT);
const userScrolled = ref(false);
const manualTab = ref<TabId | null>(null);
const logRef = ref<HTMLElement | null>(null);

const activeTab = computed(() => manualTab.value ?? autoTab.value);
const filteredEvents = computed(() => filterEvents(activeTab.value));

// Reset manual tab when auto-tab changes (route navigation)
watch(autoTab, () => {
  manualTab.value = null;
});

// Auto-scroll to bottom when new events arrive
watch(filteredEvents, () => {
  if (!userScrolled.value && logRef.value) {
    nextTick(() => {
      if (logRef.value) {
        logRef.value.scrollTop = logRef.value.scrollHeight;
      }
    });
  }
});

function handleScroll() {
  if (!logRef.value) return;
  const { scrollTop, scrollHeight, clientHeight } = logRef.value;
  const atBottom = scrollHeight - scrollTop - clientHeight < 40;
  userScrolled.value = !atBottom;
}

function handleTabClick(tabId: TabId) {
  manualTab.value = tabId === autoTab.value ? null : tabId;
}

function handleClear() {
  manualTab.value = null;
  ws.clearEvents();
}

// Resize handle
let resizing = false;
let startY = 0;
let startHeight = 0;

function handleResizeStart(e: MouseEvent | TouchEvent) {
  e.preventDefault();
  resizing = true;
  startY = "touches" in e ? e.touches[0].clientY : e.clientY;
  startHeight = panelHeight.value;

  const handleMove = (ev: MouseEvent | TouchEvent) => {
    if (!resizing) return;
    const currentY =
      "touches" in ev
        ? (ev as TouchEvent).touches[0].clientY
        : (ev as MouseEvent).clientY;
    const delta = startY - currentY;
    panelHeight.value = Math.min(
      MAX_HEIGHT,
      Math.max(MIN_HEIGHT, startHeight + delta),
    );
  };

  const handleEnd = () => {
    resizing = false;
    document.removeEventListener("mousemove", handleMove);
    document.removeEventListener("mouseup", handleEnd);
    document.removeEventListener("touchmove", handleMove);
    document.removeEventListener("touchend", handleEnd);
  };

  document.addEventListener("mousemove", handleMove);
  document.addEventListener("mouseup", handleEnd);
  document.addEventListener("touchmove", handleMove);
  document.addEventListener("touchend", handleEnd);
}

function eventKey(event: PipelineEvent, index: number): string {
  return `${event.job_id}:${event.timestamp}:${index}`;
}
</script>

<template>
  <div
    class="border-t border-base-300 bg-base-100"
    :style="{ height: expanded ? `${panelHeight + 32}px` : '32px' }"
  >
    <!-- Resize handle -->
    <div
      v-if="expanded"
      class="flex h-2 cursor-row-resize items-center justify-center hover:bg-base-300"
      @mousedown="handleResizeStart"
      @touchstart="handleResizeStart"
      role="separator"
      aria-orientation="horizontal"
      aria-label="Resize panel"
    >
      <div class="h-0.5 w-8 rounded-full bg-base-300" />
    </div>

    <!-- Collapsed bar -->
    <button
      type="button"
      class="flex h-8 w-full items-center gap-3 px-3 text-xs hover:bg-base-200"
      @click="expanded = !expanded"
      :aria-label="expanded ? 'Collapse event panel' : 'Expand event panel'"
      :aria-expanded="expanded"
    >
      <span
        :class="[
          'h-2 w-2 shrink-0 rounded-full',
          ws.isConnected ? 'bg-success' : 'bg-error',
        ]"
        :aria-label="ws.isConnected ? 'Connected' : 'Disconnected'"
      />
      <span class="shrink-0 text-base-content/60">
        {{ ws.activeJobCount > 0
          ? `${ws.activeJobCount} job${ws.activeJobCount > 1 ? 's' : ''} running`
          : 'Idle' }}
      </span>
      <span v-if="ws.lastEvent" class="truncate text-base-content/60">
        {{ ws.lastEvent.message }}
      </span>
      <span class="ml-auto shrink-0">
        <ChevronUp v-if="expanded" class="h-3 w-3" />
        <ChevronDown v-else class="h-3 w-3" />
      </span>
    </button>

    <!-- Expanded event log -->
    <div
      v-if="expanded"
      class="flex flex-col"
      :style="{ height: `${panelHeight - 8}px` }"
    >
      <!-- Tab bar + Clear -->
      <div class="flex items-center gap-1 border-b border-base-300 px-2 py-1">
        <div class="flex flex-1 items-center gap-1 overflow-x-auto">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            type="button"
            :class="[
              'shrink-0 rounded-sm px-2 py-0.5 text-xs font-medium transition-colors',
              activeTab === tab.id
                ? 'bg-base-300 text-base-content'
                : 'text-base-content/60 hover:text-base-content',
            ]"
            @click.stop="handleTabClick(tab.id)"
          >
            <span
              v-if="tab.status"
              :class="['mr-1', STATUS_COLORS[tab.status] ?? '']"
            >
              {{ STATUS_ICONS[tab.status] }}
            </span>
            {{ tab.label }}
          </button>
        </div>
        <button
          class="btn btn-ghost btn-xs gap-1"
          @click="handleClear"
          aria-label="Clear events"
        >
          <Trash2 class="h-3 w-3" />
          Clear
        </button>
      </div>

      <!-- Event log -->
      <div
        ref="logRef"
        class="flex-1 overflow-auto"
        @scroll="handleScroll"
      >
        <div
          v-if="filteredEvents.length === 0"
          class="flex h-full items-center justify-center text-xs text-base-content/60"
        >
          No events yet
        </div>
        <div
          v-for="(event, i) in filteredEvents"
          :key="eventKey(event, i)"
          class="flex gap-3 px-3 py-1 text-xs font-mono hover:bg-base-200/50"
        >
          <span class="shrink-0 text-base-content/60">
            {{ formatTime(event.timestamp) }}
          </span>
          <span
            :class="[
              'shrink-0 w-20',
              EVENT_CLASSES[event.event_type] ?? 'text-base-content/60',
            ]"
          >
            {{ event.event_type }}
          </span>
          <span class="shrink-0 w-16 text-base-content/60">
            {{ event.step }}
          </span>
          <span class="truncate">{{ event.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
