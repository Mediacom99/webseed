<script setup lang="ts">
import type { BusinessSummary } from "~/types";

const props = defineProps<{
  selectedIds: Set<string>;
  businesses: BusinessSummary[];
}>();

const emit = defineEmits<{
  "action-complete": [];
}>();

const pipeline = usePipeline();
const { blacklistAdd, hardDelete } = useBusinessActions();
const toast = useToast();

const blacklistConfirmRef = ref<{ open: () => void; close: () => void } | null>(null);
const deleteConfirmRef = ref<{ open: () => void; close: () => void } | null>(null);

const pending = reactive<Record<string, boolean>>({});

// BUG FIX: Added 'searched' -> 'enrich' mapping (was missing in React version)
const STATUS_TO_NEXT_ACTION: Record<
  string,
  { label: string; step: string }
> = {
  searched: { label: "Enrich", step: "enrich" },
  enriched: { label: "Generate", step: "generate" },
  generated: { label: "Test", step: "test" },
  tested: { label: "Deploy", step: "deploy" },
  deployed: { label: "Email", step: "email" },
  error_enrich: { label: "Retry Enrich", step: "enrich" },
  error_generate: { label: "Retry Generate", step: "generate" },
  error_test: { label: "Retry Test", step: "test" },
  error_deploy: { label: "Retry Deploy", step: "deploy" },
  error_email: { label: "Retry Email", step: "email" },
};

const selectedBusinesses = computed(() =>
  props.businesses.filter((b) => props.selectedIds.has(b.place_id)),
);

const availableActions = computed(() => {
  const actions = new Map<string, { label: string; step: string; placeIds: string[] }>();

  for (const biz of selectedBusinesses.value) {
    const action = STATUS_TO_NEXT_ACTION[biz.status];
    if (!action) continue;

    const existing = actions.get(action.step);
    if (existing) {
      existing.placeIds.push(biz.place_id);
    } else {
      actions.set(action.step, {
        label: action.label,
        step: action.step,
        placeIds: [biz.place_id],
      });
    }
  }

  return Array.from(actions.values());
});

const STEP_TO_TRIGGER: Record<string, (ids: string[]) => Promise<unknown>> = {
  enrich: (ids) => pipeline.triggerEnrich(ids),
  generate: (ids) => pipeline.triggerGenerate(ids),
  test: (ids) => pipeline.triggerTest(ids),
  deploy: (ids) => pipeline.triggerDeploy(ids),
  email: (ids) => pipeline.triggerEmail(ids),
};

async function handleAction(action: { label: string; step: string; placeIds: string[] }) {
  const trigger = STEP_TO_TRIGGER[action.step];
  if (!trigger) return;

  pending[action.step] = true;
  try {
    await trigger(action.placeIds);
    toast.push(
      `${action.label} started for ${action.placeIds.length} businesses`,
      "success",
    );
    emit("action-complete");
  } catch (e) {
    toast.push(
      e instanceof Error ? e.message : `${action.label} failed`,
      "error",
    );
  } finally {
    pending[action.step] = false;
  }
}

async function handleBlacklist() {
  pending.blacklist = true;
  try {
    await Promise.all(Array.from(props.selectedIds).map((id) => blacklistAdd(id)));
    toast.push(`${props.selectedIds.size} businesses blacklisted`, "success");
    emit("action-complete");
  } catch (e) {
    toast.push(e instanceof Error ? e.message : "Blacklist failed", "error");
  } finally {
    pending.blacklist = false;
  }
}

async function handleDelete() {
  pending.delete = true;
  try {
    await hardDelete(Array.from(props.selectedIds));
    toast.push(`${props.selectedIds.size} businesses deleted`, "success");
    emit("action-complete");
  } catch (e) {
    toast.push(e instanceof Error ? e.message : "Delete failed", "error");
  } finally {
    pending.delete = false;
  }
}
</script>

<template>
  <div
    v-if="selectedIds.size > 0"
    class="sticky bottom-0 z-10 flex flex-wrap items-center gap-3 rounded-lg border border-base-300 bg-base-200 p-3"
  >
    <span class="text-sm font-medium">
      {{ selectedIds.size }} selected
    </span>

    <!-- Pipeline action buttons -->
    <button
      v-for="action in availableActions"
      :key="action.step"
      class="btn btn-primary btn-sm"
      :disabled="pending[action.step]"
      @click="handleAction(action)"
    >
      <span v-if="pending[action.step]" class="loading loading-spinner loading-xs" />
      {{ action.label }} ({{ action.placeIds.length }})
    </button>

    <div class="flex-1" />

    <!-- Destructive actions -->
    <button
      class="btn btn-warning btn-outline btn-sm"
      :disabled="pending.blacklist"
      @click="blacklistConfirmRef?.open()"
    >
      Blacklist
    </button>

    <button
      class="btn btn-error btn-outline btn-sm"
      :disabled="pending.delete"
      @click="deleteConfirmRef?.open()"
    >
      Delete
    </button>

    <SharedConfirmDialog
      ref="blacklistConfirmRef"
      title="Blacklist businesses?"
      :description="`Blacklist ${selectedIds.size} businesses? They will be excluded from future pipeline runs.`"
      confirm-label="Blacklist"
      confirm-class="btn-warning"
      @confirm="handleBlacklist"
    />

    <SharedConfirmDialog
      ref="deleteConfirmRef"
      title="Delete businesses?"
      :description="`Permanently delete ${selectedIds.size} businesses? This cannot be undone.`"
      confirm-label="Delete"
      confirm-class="btn-error"
      @confirm="handleDelete"
    />
  </div>
</template>
