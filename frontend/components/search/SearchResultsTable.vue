<script setup lang="ts">
import { ArrowUpDown } from "lucide-vue-next";
import type { BusinessSummary, SortDir } from "~/types";

const props = defineProps<{
  results: BusinessSummary[];
}>();

const selected = defineModel<Set<string>>("selected", {
  default: () => new Set(),
});

const sortField = ref<"rating" | "reviews" | "lead_score" | null>(null);
const sortDir = ref<SortDir>("desc");

function toggleSort(field: "rating" | "reviews" | "lead_score") {
  if (sortField.value === field) {
    sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  } else {
    sortField.value = field;
    sortDir.value = "desc";
  }
}

const sorted = computed(() => {
  if (!sortField.value) return props.results;
  const field = sortField.value;
  const dir = sortDir.value === "asc" ? 1 : -1;
  return [...props.results].sort(
    (a, b) => ((a[field] ?? 0) - (b[field] ?? 0)) * dir,
  );
});

const allSelected = computed(
  () =>
    props.results.length > 0 &&
    props.results.every((r) => selected.value.has(r.place_id)),
);

function toggleAll() {
  if (allSelected.value) {
    selected.value = new Set();
  } else {
    selected.value = new Set(props.results.map((r) => r.place_id));
  }
}

function toggleRow(placeId: string) {
  const next = new Set(selected.value);
  if (next.has(placeId)) {
    next.delete(placeId);
  } else {
    next.add(placeId);
  }
  selected.value = next;
}
</script>

<template>
  <div class="overflow-x-auto">
    <table class="table table-zebra w-full">
      <thead>
        <tr>
          <th>
            <input
              type="checkbox"
              class="checkbox checkbox-sm"
              :checked="allSelected"
              @change="toggleAll"
              aria-label="Select all"
            />
          </th>
          <th>Name</th>
          <th>Category</th>
          <th class="cursor-pointer" @click="toggleSort('rating')">
            <span class="flex items-center gap-1">
              Rating
              <ArrowUpDown class="h-3 w-3" />
            </span>
          </th>
          <th class="cursor-pointer" @click="toggleSort('reviews')">
            <span class="flex items-center gap-1">
              Reviews
              <ArrowUpDown class="h-3 w-3" />
            </span>
          </th>
          <th>Address</th>
          <th class="cursor-pointer" @click="toggleSort('lead_score')">
            <span class="flex items-center gap-1">
              Pre-score
              <ArrowUpDown class="h-3 w-3" />
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in sorted" :key="r.place_id">
          <td @click.stop>
            <input
              type="checkbox"
              class="checkbox checkbox-sm"
              :checked="selected.has(r.place_id)"
              @change="toggleRow(r.place_id)"
            />
          </td>
          <td class="font-medium">{{ r.name }}</td>
          <td class="text-base-content/70">{{ r.category }}</td>
          <td>{{ r.rating > 0 ? r.rating.toFixed(1) : "-" }}</td>
          <td>{{ r.reviews }}</td>
          <td class="max-w-[200px] truncate text-base-content/70">
            {{ r.address }}
          </td>
          <td>{{ r.lead_score }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
