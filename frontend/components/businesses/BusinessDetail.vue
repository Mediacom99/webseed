<script setup lang="ts">
import {
  ArrowLeft,
  Star,
  ShieldOff,
  Shield,
  Trash2,
} from "lucide-vue-next";
import type { BusinessDetail } from "~/types";

const props = defineProps<{
  business: BusinessDetail;
}>();

const emit = defineEmits<{
  refresh: [];
}>();

const pipeline = usePipeline();
const { blacklistAdd, blacklistRemove, deleteBusiness } = useBusinessActions();
const toast = useToast();

const deleteConfirmRef = ref<{ open: () => void; close: () => void } | null>(null);

const RUNNING_STATUSES = new Set([
  "running_enrich",
  "running_generate",
  "running_test",
  "running_deploy",
  "running_email",
]);

const NO_ACTION_STATUSES = new Set([
  "emailed",
  "email_queued",
  "opted_out",
]);

const STATUS_TO_NEXT: Record<string, { label: string; step: string }> = {
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
  error_run: { label: "Retry Enrich", step: "enrich" },
};

const STEP_TO_TRIGGER: Record<string, (ids: string[]) => Promise<unknown>> = {
  enrich: (ids) => pipeline.triggerEnrich(ids),
  generate: (ids) => pipeline.triggerGenerate(ids),
  test: (ids) => pipeline.triggerTest(ids),
  deploy: (ids) => pipeline.triggerDeploy(ids),
  email: (ids) => pipeline.triggerEmail(ids),
};

const isRunning = computed(() => RUNNING_STATUSES.has(props.business.status));
const noAction = computed(() => NO_ACTION_STATUSES.has(props.business.status));
const nextAction = computed(() => STATUS_TO_NEXT[props.business.status]);
const isOptedOut = computed(() => props.business.status === "opted_out");

const actionPending = ref(false);
const blacklistPending = ref(false);

async function handleNextAction() {
  if (!nextAction.value) return;
  const trigger = STEP_TO_TRIGGER[nextAction.value.step];
  if (!trigger) return;

  actionPending.value = true;
  try {
    await trigger([props.business.place_id]);
    toast.push(`${nextAction.value.label} started`, "success");
    emit("refresh");
  } catch (e) {
    toast.push(e instanceof Error ? e.message : "Action failed", "error");
  } finally {
    actionPending.value = false;
  }
}

async function handleBlacklistToggle() {
  blacklistPending.value = true;
  try {
    if (isOptedOut.value) {
      await blacklistRemove(props.business.place_id);
      toast.push("Removed from blacklist", "success");
    } else {
      await blacklistAdd(props.business.place_id);
      toast.push("Added to blacklist", "success");
    }
    emit("refresh");
  } catch (e) {
    toast.push(e instanceof Error ? e.message : "Action failed", "error");
  } finally {
    blacklistPending.value = false;
  }
}

async function handleDelete() {
  try {
    await deleteBusiness(props.business.place_id);
    toast.push("Business deleted", "success");
    navigateTo("/businesses");
  } catch (e) {
    toast.push(e instanceof Error ? e.message : "Delete failed", "error");
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <NuxtLink to="/businesses" class="link link-primary text-sm flex items-center gap-1 mb-2">
        <ArrowLeft class="h-4 w-4" />
        Businesses
      </NuxtLink>

      <div class="flex flex-wrap items-center gap-3">
        <h1 class="text-2xl font-semibold">{{ business.name }}</h1>
        <SharedStatusBadge :status="business.status" />
        <span v-if="business.primary_type" class="text-base-content/60 text-sm">
          {{ business.primary_type.replace(/_/g, " ") }}
        </span>
        <span v-if="business.rating > 0" class="flex items-center gap-1 text-sm">
          <Star class="h-4 w-4 text-warning" />
          {{ business.rating.toFixed(1) }}
          <span class="text-base-content/60">({{ business.reviews }})</span>
        </span>
      </div>
    </div>

    <!-- Pipeline Graph -->
    <SharedPipelineGraph :status="business.status" />

    <!-- Action Buttons -->
    <div class="flex flex-wrap items-center gap-2">
      <!-- Next step button -->
      <button
        v-if="nextAction && !isRunning && !noAction"
        class="btn btn-primary btn-sm"
        :disabled="actionPending"
        @click="handleNextAction"
      >
        <span v-if="actionPending" class="loading loading-spinner loading-xs" />
        {{ nextAction.label }}
      </button>

      <button
        v-if="isRunning"
        class="btn btn-sm btn-disabled"
        disabled
      >
        <span class="loading loading-spinner loading-xs" />
        Running...
      </button>

      <div class="flex-1" />

      <!-- Blacklist toggle -->
      <button
        class="btn btn-outline btn-sm"
        :class="isOptedOut ? 'btn-success' : 'btn-warning'"
        :disabled="blacklistPending"
        @click="handleBlacklistToggle"
      >
        <Shield v-if="isOptedOut" class="h-4 w-4" />
        <ShieldOff v-else class="h-4 w-4" />
        {{ isOptedOut ? "Unblacklist" : "Blacklist" }}
      </button>

      <!-- Delete -->
      <button
        class="btn btn-error btn-outline btn-sm"
        @click="deleteConfirmRef?.open()"
      >
        <Trash2 class="h-4 w-4" />
        Delete
      </button>
    </div>

    <!-- Info Cards -->
    <BusinessesInfoCards :business="business" @refresh="$emit('refresh')" />

    <SharedConfirmDialog
      ref="deleteConfirmRef"
      title="Delete business?"
      :description="`Permanently delete ${business.name}? This cannot be undone.`"
      confirm-label="Delete"
      confirm-class="btn-error"
      @confirm="handleDelete"
    />
  </div>
</template>
