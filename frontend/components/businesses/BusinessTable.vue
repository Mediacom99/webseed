<script setup lang="ts">
import { ArrowUpDown, ExternalLink } from "lucide-vue-next";
import type { BusinessSummary, SortDir } from "~/types";

const props = defineProps<{
  businesses: BusinessSummary[];
  searchText: string;
}>();

const selectedIds = defineModel<Set<string>>("selectedIds", {
  default: () => new Set(),
});

const sortField = ref<"name" | "rating" | "lead_score" | null>(null);
const sortDir = ref<SortDir>("desc");

function toggleSort(field: "name" | "rating" | "lead_score") {
  if (sortField.value === field) {
    sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  } else {
    sortField.value = field;
    sortDir.value = field === "name" ? "asc" : "desc";
  }
}

const filtered = computed(() => {
  let result = props.businesses;

  if (props.searchText) {
    const q = props.searchText.toLowerCase();
    result = result.filter((b) => b.name.toLowerCase().includes(q));
  }

  if (sortField.value) {
    const field = sortField.value;
    const dir = sortDir.value === "asc" ? 1 : -1;
    result = [...result].sort((a, b) => {
      const va = a[field];
      const vb = b[field];
      if (typeof va === "string" && typeof vb === "string") {
        return va.localeCompare(vb) * dir;
      }
      return (((va as number) ?? 0) - ((vb as number) ?? 0)) * dir;
    });
  }

  return result;
});

const allSelected = computed(
  () =>
    filtered.value.length > 0 &&
    filtered.value.every((b) => selectedIds.value.has(b.place_id)),
);

function toggleAll() {
  if (allSelected.value) {
    selectedIds.value = new Set();
  } else {
    selectedIds.value = new Set(filtered.value.map((b) => b.place_id));
  }
}

function toggleRow(placeId: string) {
  const next = new Set(selectedIds.value);
  if (next.has(placeId)) {
    next.delete(placeId);
  } else {
    next.add(placeId);
  }
  selectedIds.value = next;
}
</script>

<template>
  <div class="overflow-x-auto">
    <!-- Empty state -->
    <div
      v-if="filtered.length === 0"
      class="py-12 text-center text-base-content/60"
    >
      No businesses match this filter
    </div>

    <table v-else class="table table-zebra w-full">
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
          <th class="cursor-pointer" @click="toggleSort('name')">
            <span class="flex items-center gap-1">
              Name
              <ArrowUpDown class="h-3 w-3" />
            </span>
          </th>
          <th>Status</th>
          <th>Error</th>
          <th>Category</th>
          <th class="cursor-pointer" @click="toggleSort('rating')">
            <span class="flex items-center gap-1">
              Rating
              <ArrowUpDown class="h-3 w-3" />
            </span>
          </th>
          <th class="cursor-pointer" @click="toggleSort('lead_score')">
            <span class="flex items-center gap-1">
              Score
              <ArrowUpDown class="h-3 w-3" />
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="b in filtered"
          :key="b.place_id"
          class="cursor-pointer hover"
          @click="navigateTo(`/businesses/${b.place_id}`)"
        >
          <td @click.stop>
            <input
              type="checkbox"
              class="checkbox checkbox-sm"
              :checked="selectedIds.has(b.place_id)"
              @change="toggleRow(b.place_id)"
            />
          </td>
          <td class="font-medium">{{ b.name }}</td>
          <td>
            <SharedStatusBadge :status="b.status" />
          </td>
          <td class="max-w-[150px] truncate text-error text-xs">
            {{ b.error_detail || "" }}
          </td>
          <td class="text-base-content/70">{{ b.category }}</td>
          <td>{{ b.rating > 0 ? b.rating.toFixed(1) : "-" }}</td>
          <td>{{ b.lead_score ?? "-" }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
