<script setup lang="ts">
const props = defineProps<{
  status: string;
}>();

const badgeClass = computed(() => {
  const s = props.status;

  if (s.startsWith("running_")) return "badge badge-info animate-pulse";
  if (s.startsWith("error_")) return "badge badge-error";

  const map: Record<string, string> = {
    searched: "badge badge-info",
    enriched: "badge bg-purple-600 text-white border-purple-600",
    generated: "badge badge-success",
    tested: "badge bg-teal-600 text-white border-teal-600",
    deployed: "badge badge-success badge-outline",
    email_queued: "badge badge-warning",
    emailed: "badge badge-accent",
    opted_out: "badge badge-ghost",
  };

  return map[s] ?? "badge";
});

const label = computed(() =>
  props.status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
);
</script>

<template>
  <span :class="badgeClass" class="badge-sm">{{ label }}</span>
</template>
