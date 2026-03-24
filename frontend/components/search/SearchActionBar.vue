<script setup lang="ts">
const props = defineProps<{
  selectedIds: Set<string>;
}>();

const emit = defineEmits<{
  "action-complete": [];
}>();

const { triggerEnrich } = usePipeline();
const { blacklistAdd } = useBusinessActions();
const toast = useToast();

const enrichPending = ref(false);
const blacklistPending = ref(false);
const confirmRef = ref<{ open: () => void; close: () => void } | null>(null);

async function handleEnrich() {
  if (props.selectedIds.size === 0) return;
  enrichPending.value = true;
  try {
    await triggerEnrich(Array.from(props.selectedIds));
    toast.push(
      `${props.selectedIds.size} businesses sent to enrich`,
      "success",
    );
    emit("action-complete");
  } catch (e) {
    toast.push(
      e instanceof Error ? e.message : "Enrich failed",
      "error",
    );
  } finally {
    enrichPending.value = false;
  }
}

async function handleBlacklist() {
  blacklistPending.value = true;
  try {
    await Promise.all(Array.from(props.selectedIds).map((id) => blacklistAdd(id)));
    toast.push(
      `${props.selectedIds.size} businesses blacklisted`,
      "success",
    );
    emit("action-complete");
  } catch (e) {
    toast.push(
      e instanceof Error ? e.message : "Blacklist failed",
      "error",
    );
  } finally {
    blacklistPending.value = false;
  }
}
</script>

<template>
  <div
    v-if="selectedIds.size > 0"
    class="sticky bottom-0 z-10 flex items-center gap-3 rounded-lg border border-base-300 bg-base-200 p-3"
  >
    <span class="text-sm font-medium">
      {{ selectedIds.size }} selected
    </span>

    <button
      class="btn btn-primary btn-sm"
      :disabled="enrichPending"
      @click="handleEnrich"
    >
      <span v-if="enrichPending" class="loading loading-spinner loading-xs" />
      Enrich Selected
    </button>

    <button
      class="btn btn-error btn-outline btn-sm"
      :disabled="blacklistPending"
      @click="confirmRef?.open()"
    >
      Blacklist Selected
    </button>

    <SharedConfirmDialog
      ref="confirmRef"
      title="Blacklist businesses?"
      :description="`Are you sure you want to blacklist ${selectedIds.size} businesses? This will exclude them from future pipeline runs.`"
      confirm-label="Blacklist"
      confirm-class="btn-error"
      @confirm="handleBlacklist"
    />
  </div>
</template>
