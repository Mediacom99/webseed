<script setup lang="ts">
import { Save } from "lucide-vue-next";
import { humanizeKey } from "~/utils/formatters";

const { settings, pending, error, refresh } = useSettingsList("config");
const { updateSetting } = useSettingActions();
const toast = useToast();

const edits = ref<Map<string, string>>(new Map());
const saving = ref<Record<string, boolean>>({});
const focusedKey = ref<string | null>(null);

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

function isDirty(key: string): boolean {
  const original = settings.value.find((s) => s.key === key);
  const current = edits.value.get(key);
  return !!original && current !== undefined && current !== original.value;
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
    toast.push(`Saved ${humanizeKey(key)}`, "success");
  } catch (e) {
    toast.push(e instanceof Error ? e.message : "Save failed", "error");
  } finally {
    saving.value[key] = false;
  }
}
</script>

<template>
  <!-- Loading -->
  <div v-if="pending && settings.length === 0" class="space-y-2">
    <div v-for="i in 5" :key="i" class="skeleton h-12 w-full" />
  </div>

  <!-- Error -->
  <div v-else-if="error && settings.length === 0" class="py-8 text-center">
    <p class="text-error mb-2">{{ error.message }}</p>
    <button class="btn btn-primary btn-sm" @click="refresh">Retry</button>
  </div>

  <div v-else class="overflow-x-auto">
    <table class="table w-full">
      <thead>
        <tr>
          <th>Setting</th>
          <th>Value</th>
          <th class="w-16" />
        </tr>
      </thead>
      <tbody>
        <tr v-for="setting in settings" :key="setting.key">
          <td class="align-top">
            <div class="flex items-center gap-2">
              <span class="font-medium text-sm">
                {{ humanizeKey(setting.key) }}
              </span>
              <span
                v-if="isDirty(setting.key)"
                class="h-2 w-2 rounded-full bg-warning"
                title="Unsaved"
              />
            </div>
            <p
              v-if="focusedKey === setting.key && setting.description"
              class="mt-1 text-xs text-base-content/60"
            >
              {{ setting.description }}
            </p>
          </td>
          <td>
            <input
              :value="edits.get(setting.key) ?? setting.value"
              @input="edits = new Map(edits).set(setting.key, ($event.target as HTMLInputElement).value)"
              @focus="focusedKey = setting.key"
              @blur="focusedKey = null"
              class="input input-bordered input-sm w-full"
            />
          </td>
          <td>
            <button
              class="btn btn-ghost btn-xs"
              :disabled="!isDirty(setting.key) || saving[setting.key]"
              @click="handleSave(setting.key)"
            >
              <span
                v-if="saving[setting.key]"
                class="loading loading-spinner loading-xs"
              />
              <Save v-else class="h-4 w-4" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
