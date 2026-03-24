<script setup lang="ts">
import { Save } from "lucide-vue-next";

const { settings, pending, error, refresh } = useSettingsList("prompt");
const { updateSetting } = useSettingActions();
const toast = useToast();

const edits = ref<Map<string, string>>(new Map());
const saving = ref<Record<string, boolean>>({});

// Initialize edits from settings
watch(
  settings,
  (newSettings) => {
    if (edits.value.size === 0 && newSettings.length > 0) {
      const map = new Map<string, string>();
      for (const s of newSettings) {
        map.set(s.key, s.value);
      }
      edits.value = map;
    }
  },
  { immediate: true },
);

interface PromptGroup {
  label: string;
  prefix: string;
  keys: string[];
}

const PROMPT_GROUPS: PromptGroup[] = [
  {
    label: "Site Generation",
    prefix: "prompt.generate",
    keys: ["prompt.generate", "prompt.generate_system"],
  },
  {
    label: "Code Review",
    prefix: "prompt.review",
    keys: ["prompt.review", "prompt.review_system"],
  },
  {
    label: "Visual Test",
    prefix: "prompt.visual",
    keys: ["prompt.visual_test", "prompt.visual_test_system"],
  },
  {
    label: "Fix HTML",
    prefix: "prompt.fix",
    keys: ["prompt.fix", "prompt.fix_system"],
  },
  {
    label: "Email Generation",
    prefix: "prompt.email",
    keys: ["prompt.email", "prompt.email_system"],
  },
];

function getGroupSettings(group: PromptGroup) {
  return settings.value.filter(
    (s) =>
      group.keys.includes(s.key) ||
      s.key.startsWith(group.prefix),
  );
}

function isDirty(key: string): boolean {
  const original = settings.value.find((s) => s.key === key);
  const current = edits.value.get(key);
  return !!original && current !== undefined && current !== original.value;
}

function unsavedCount(group: PromptGroup): number {
  return getGroupSettings(group).filter((s) => isDirty(s.key)).length;
}

async function handleSave(key: string) {
  const value = edits.value.get(key);
  if (value === undefined) return;

  saving.value[key] = true;
  try {
    await updateSetting(key, value);
    await refresh();
    // Re-sync this key's edit with the refreshed server value
    const updated = settings.value.find((s) => s.key === key);
    if (updated) edits.value.set(key, updated.value);
    toast.push(`Saved ${key}`, "success");
  } catch (e) {
    toast.push(e instanceof Error ? e.message : "Save failed", "error");
  } finally {
    saving.value[key] = false;
  }
}

// Group ungrouped prompts
const ungroupedSettings = computed(() => {
  const groupedKeys = new Set(PROMPT_GROUPS.flatMap((g) => g.keys));
  return settings.value.filter(
    (s) =>
      !groupedKeys.has(s.key) &&
      !PROMPT_GROUPS.some((g) => s.key.startsWith(g.prefix)),
  );
});
</script>

<template>
  <!-- Loading -->
  <div v-if="pending && settings.length === 0" class="space-y-4">
    <div v-for="i in 3" :key="i" class="skeleton h-20 w-full" />
  </div>

  <!-- Error -->
  <div v-else-if="error && settings.length === 0" class="py-8 text-center">
    <p class="text-error mb-2">{{ error.message }}</p>
    <button class="btn btn-primary btn-sm" @click="refresh">Retry</button>
  </div>

  <div v-else class="space-y-2">
    <div
      v-for="group in PROMPT_GROUPS"
      :key="group.label"
      class="collapse collapse-arrow bg-base-200"
    >
      <input type="checkbox" />
      <div class="collapse-title font-medium flex items-center gap-2">
        {{ group.label }}
        <span class="badge badge-sm">{{ getGroupSettings(group).length }}</span>
        <span
          v-if="unsavedCount(group) > 0"
          class="badge badge-warning badge-sm"
        >
          {{ unsavedCount(group) }} unsaved
        </span>
      </div>
      <div class="collapse-content space-y-4">
        <div
          v-for="setting in getGroupSettings(group)"
          :key="setting.key"
          class="space-y-1"
        >
          <div class="flex items-center justify-between">
            <label class="label-text text-sm font-medium flex items-center gap-2">
              {{ setting.key }}
              <span
                v-if="isDirty(setting.key)"
                class="h-2 w-2 rounded-full bg-warning"
                title="Unsaved changes"
              />
            </label>
            <button
              class="btn btn-ghost btn-xs"
              :disabled="!isDirty(setting.key) || saving[setting.key]"
              @click="handleSave(setting.key)"
            >
              <span
                v-if="saving[setting.key]"
                class="loading loading-spinner loading-xs"
              />
              <Save v-else class="h-3 w-3" />
            </button>
          </div>
          <textarea
            :value="edits.get(setting.key) ?? setting.value"
            @input="edits = new Map(edits).set(setting.key, ($event.target as HTMLTextAreaElement).value)"
            class="textarea textarea-bordered w-full font-mono text-sm"
            rows="6"
          />
          <p v-if="setting.description" class="text-xs text-base-content/60">
            {{ setting.description }}
          </p>
        </div>
      </div>
    </div>

    <!-- Ungrouped -->
    <div
      v-if="ungroupedSettings.length > 0"
      class="collapse collapse-arrow bg-base-200"
    >
      <input type="checkbox" />
      <div class="collapse-title font-medium">
        Other
        <span class="badge badge-sm">{{ ungroupedSettings.length }}</span>
      </div>
      <div class="collapse-content space-y-4">
        <div
          v-for="setting in ungroupedSettings"
          :key="setting.key"
          class="space-y-1"
        >
          <div class="flex items-center justify-between">
            <label class="label-text text-sm font-medium flex items-center gap-2">
              {{ setting.key }}
              <span
                v-if="isDirty(setting.key)"
                class="h-2 w-2 rounded-full bg-warning"
              />
            </label>
            <button
              class="btn btn-ghost btn-xs"
              :disabled="!isDirty(setting.key) || saving[setting.key]"
              @click="handleSave(setting.key)"
            >
              <span
                v-if="saving[setting.key]"
                class="loading loading-spinner loading-xs"
              />
              <Save v-else class="h-3 w-3" />
            </button>
          </div>
          <textarea
            :value="edits.get(setting.key) ?? setting.value"
            @input="edits = new Map(edits).set(setting.key, ($event.target as HTMLTextAreaElement).value)"
            class="textarea textarea-bordered w-full font-mono text-sm"
            rows="6"
          />
        </div>
      </div>
    </div>
  </div>
</template>
