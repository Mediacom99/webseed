<script setup lang="ts">
const lastJobId = ref<string | null>(null);
const selected = ref<Set<string>>(new Set());
const statusFilter = ref<string | undefined>("searched");

const { businesses, pending, refresh } = useBusinessList(statusFilter);
const ws = useWebSocketStore();

// Refetch when new search step_done event arrives
const seenEventCount = ref(ws.events.length);
watch(
  () => ws.events.length,
  (len) => {
    const newEvents = ws.events.slice(seenEventCount.value);
    seenEventCount.value = len;
    const searchDone = newEvents.find(
      (e) =>
        e.event_type === "step_done" &&
        e.step === "search" &&
        (lastJobId.value === null || e.job_id === lastJobId.value),
    );
    if (searchDone) refresh();
  },
);

function handleActionComplete() {
  selected.value = new Set();
  refresh();
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold">Search</h1>

    <div class="card bg-base-200">
      <div class="card-body">
        <h2 class="card-title text-lg">Find Businesses</h2>
        <SearchForm @job-started="lastJobId = $event" />
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="pending && businesses.length === 0" class="space-y-2">
      <div class="skeleton h-8 w-48" />
      <div class="skeleton h-64 w-full" />
    </div>

    <!-- No results -->
    <p
      v-else-if="lastJobId && businesses.length === 0"
      class="py-8 text-center text-base-content/60"
    >
      No results
    </p>

    <!-- Results -->
    <template v-else-if="businesses.length > 0">
      <div class="space-y-2">
        <h2 class="text-lg font-medium">
          Results ({{ businesses.length }})
        </h2>
        <SearchResultsTable
          :results="businesses"
          v-model:selected="selected"
        />
      </div>

      <SearchActionBar
        :selected-ids="selected"
        @action-complete="handleActionComplete"
      />
    </template>
  </div>
</template>
