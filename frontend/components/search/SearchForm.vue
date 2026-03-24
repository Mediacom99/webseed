<script setup lang="ts">
const emit = defineEmits<{
  "job-started": [jobId: string];
}>();

const { triggerSearch } = usePipeline();
const toast = useToast();

const location = ref("");
const query = ref("");
const types = ref<string[]>([]);
const showAdvanced = ref(false);
const limit = ref(10);
const minScore = ref(0);
const gridSize = ref(3);
const loading = ref(false);

async function handleSubmit() {
  if (!location.value.trim() || !query.value.trim()) return;

  loading.value = true;
  try {
    const result = await triggerSearch({
      location: location.value.trim(),
      query: query.value.trim(),
      types: types.value.length > 0 ? types.value : undefined,
      limit: limit.value,
      min_score: minScore.value,
      grid_size: gridSize.value,
    });
    emit("job-started", result.job_id);
    toast.push("Search started", "success");
  } catch (e) {
    toast.push(
      e instanceof Error ? e.message : "Search failed",
      "error",
    );
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div class="form-control">
        <label class="label" for="search-location">
          <span class="label-text">Location *</span>
        </label>
        <input
          id="search-location"
          v-model="location"
          type="text"
          placeholder="e.g. Milano, Roma..."
          class="input input-bordered w-full"
          required
        />
      </div>

      <div class="form-control">
        <label class="label" for="search-query">
          <span class="label-text">Query *</span>
        </label>
        <input
          id="search-query"
          v-model="query"
          type="text"
          placeholder="e.g. ristorante, parrucchiere..."
          class="input input-bordered w-full"
          required
        />
      </div>
    </div>

    <SearchTypesMultiSelect v-model="types" />

    <!-- Advanced options -->
    <details @toggle="showAdvanced = ($event.target as HTMLDetailsElement).open">
      <summary class="cursor-pointer text-sm font-medium text-base-content/60 hover:text-base-content">
        Advanced Options
      </summary>
      <div class="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div class="form-control">
          <label class="label" for="search-limit">
            <span class="label-text">Limit</span>
          </label>
          <input
            id="search-limit"
            v-model.number="limit"
            type="number"
            min="1"
            max="100"
            class="input input-bordered input-sm w-full"
          />
        </div>

        <div class="form-control">
          <label class="label" for="search-min-score">
            <span class="label-text">Min Score</span>
          </label>
          <input
            id="search-min-score"
            v-model.number="minScore"
            type="number"
            min="0"
            max="100"
            class="input input-bordered input-sm w-full"
          />
        </div>

        <div class="form-control">
          <label class="label" for="search-grid-size">
            <span class="label-text">Grid Size</span>
          </label>
          <input
            id="search-grid-size"
            v-model.number="gridSize"
            type="number"
            min="1"
            max="10"
            class="input input-bordered input-sm w-full"
          />
        </div>
      </div>
    </details>

    <button
      type="submit"
      class="btn btn-primary"
      :disabled="loading || !location.trim() || !query.trim()"
    >
      <span v-if="loading" class="loading loading-spinner loading-sm" />
      {{ loading ? "Searching..." : "Search" }}
    </button>
  </form>
</template>
