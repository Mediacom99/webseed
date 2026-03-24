<script setup lang="ts">
import { Search, MoreHorizontal, Download } from "lucide-vue-next";
import { filterKeyToStatuses } from "~/utils/statusGroups";

const route = useRoute();
const router = useRouter();

const searchText = ref("");
const selectedIds = ref<Set<string>>(new Set());

const statusParam = computed(() => (route.query.status as string) ?? "all");

function setStatusFilter(filter: string) {
  const query = filter === "all" ? {} : { status: filter };
  router.replace({ query });
  selectedIds.value = new Set();
}

const apiStatus = computed(() => {
  const statuses = filterKeyToStatuses(statusParam.value);
  if (!statuses || statuses.length > 1) return undefined;
  return statuses[0];
});

const clientStatuses = computed(() => {
  const statuses = filterKeyToStatuses(statusParam.value);
  if (!statuses || statuses.length <= 1) return null;
  return new Set(statuses);
});

const { businesses: rawBusinesses, stats, pending, error, refresh } =
  useBusinessList(apiStatus);

const businesses = computed(() => {
  if (!clientStatuses.value) return rawBusinesses.value;
  return rawBusinesses.value.filter((b) => clientStatuses.value!.has(b.status));
});

const ws = useWebSocketStore();
const { exportCsv } = useBusinessActions();

// Refetch on new step_done events (skip persisted ones from prior sessions)
const seenEventCount = ref(ws.events.length);
watch(
  () => ws.events.length,
  (len) => {
    const newEvents = ws.events.slice(seenEventCount.value);
    seenEventCount.value = len;
    if (newEvents.some((e) => e.event_type === "step_done")) refresh();
  },
);

function handleActionComplete() {
  selectedIds.value = new Set();
  refresh();
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">Businesses</h1>
      <div class="dropdown dropdown-end">
        <div tabindex="0" role="button" class="btn btn-outline btn-sm btn-square">
          <MoreHorizontal class="h-4 w-4" />
        </div>
        <ul
          tabindex="0"
          class="dropdown-content menu rounded-box z-10 w-52 bg-base-200 p-2 shadow"
        >
          <li>
            <a @click="exportCsv()">
              <Download class="h-4 w-4" />
              Export CSV
            </a>
          </li>
        </ul>
      </div>
    </div>

    <BusinessesStatusFilterChips
      :stats="stats"
      :filter="statusParam"
      @update:filter="setStatusFilter"
    />

    <label class="input input-bordered flex items-center gap-2">
      <Search class="h-4 w-4 text-base-content/60" />
      <input
        v-model="searchText"
        type="text"
        placeholder="Search by name..."
        class="grow"
      />
    </label>

    <!-- Loading skeleton -->
    <div v-if="pending && businesses.length === 0" class="space-y-2">
      <div class="skeleton h-10 w-full" />
      <div v-for="i in 5" :key="i" class="skeleton h-12 w-full" />
    </div>

    <!-- Error state -->
    <div
      v-else-if="error"
      class="flex flex-col items-center py-12"
    >
      <p class="mb-4 text-error">{{ error.message }}</p>
      <button class="btn btn-primary btn-sm" @click="refresh">Retry</button>
    </div>

    <!-- Table -->
    <template v-else>
      <BusinessesBusinessTable
        :businesses="businesses"
        :search-text="searchText"
        v-model:selected-ids="selectedIds"
      />

      <BusinessesBulkActionBar
        :selected-ids="selectedIds"
        :businesses="businesses"
        @action-complete="handleActionComplete"
      />
    </template>
  </div>
</template>
