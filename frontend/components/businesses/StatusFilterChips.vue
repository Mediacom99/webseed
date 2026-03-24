<script setup lang="ts">
import type { StatsResponse } from "~/types";
import { STATUS_GROUPS } from "~/utils/statusGroups";

const props = defineProps<{
  stats: StatsResponse;
  filter: string;
}>();

const emit = defineEmits<{
  "update:filter": [value: string];
}>();

function getCount(group: (typeof STATUS_GROUPS)[number]): number {
  if (group.key === "all") {
    return Object.values(props.stats).reduce((a, b) => a + b, 0);
  }
  if (!group.statuses) return 0;
  return group.statuses.reduce((sum, s) => sum + (props.stats[s] ?? 0), 0);
}

const visibleGroups = computed(() =>
  STATUS_GROUPS.filter((g) => g.key === "all" || getCount(g) > 0),
);
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <button
      v-for="group in visibleGroups"
      :key="group.key"
      :class="[
        'badge cursor-pointer gap-1 transition-colors',
        props.filter === group.key
          ? 'badge-primary'
          : 'badge-outline hover:badge-primary/50',
      ]"
      @click="emit('update:filter', group.key)"
    >
      {{ group.label }}
      <span class="badge badge-xs">{{ getCount(group) }}</span>
    </button>
  </div>
</template>
