<script setup lang="ts">
import { AlertCircle } from "lucide-vue-next";

const route = useRoute();
const placeId = computed(() => route.params.placeId as string);

const { business, pending, error, refresh } = useBusinessDetail(placeId);

const ws = useWebSocketStore();

// Refetch on new WS events for this business
const seenEventCount = ref(ws.events.length);
watch(
  () => ws.events.length,
  (len) => {
    const newEvents = ws.events.slice(seenEventCount.value);
    seenEventCount.value = len;
    const relevant = newEvents.find(
      (e) =>
        (e.event_type === "step_done" || e.event_type === "step_error") &&
        e.place_id === placeId.value,
    );
    if (relevant) refresh();
  },
);
</script>

<template>
  <!-- Loading skeleton -->
  <div v-if="pending && !business" class="space-y-4">
    <div class="skeleton h-8 w-64" />
    <div class="skeleton h-6 w-32" />
    <div class="flex gap-2">
      <div v-for="i in 6" :key="i" class="skeleton h-16 w-20" />
    </div>
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div v-for="i in 4" :key="i" class="skeleton h-32" />
    </div>
  </div>

  <!-- Error state -->
  <div
    v-else-if="error"
    class="flex flex-col items-center justify-center py-12"
  >
    <AlertCircle class="mb-4 h-10 w-10 text-error" />
    <h2 class="text-lg font-semibold">Failed to load business</h2>
    <p class="mb-4 text-sm text-base-content/60">
      {{ error.message }}
    </p>
    <button class="btn btn-primary btn-sm" @click="refresh">Retry</button>
  </div>

  <!-- Not found -->
  <div
    v-else-if="!business"
    class="py-8 text-center"
  >
    <h2 class="text-lg font-semibold">Business not found</h2>
    <p class="text-base-content/60">
      No business with place ID: {{ placeId }}
    </p>
  </div>

  <!-- Business detail -->
  <BusinessesBusinessDetail
    v-else
    :business="business"
    @refresh="refresh"
  />
</template>
