import type { SettingItem } from "~/types";

export function useSettingsList(prefix: "prompt" | "config") {
  const { apiFetch } = useApi();

  const settings = ref<SettingItem[]>([]);
  const pending = ref(false);
  const error = ref<Error | null>(null);

  async function refresh() {
    pending.value = true;
    error.value = null;
    try {
      settings.value = await apiFetch<SettingItem[]>(
        `/settings?prefix=${prefix}`,
      );
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e));
    } finally {
      pending.value = false;
    }
  }

  refresh();

  return { settings, pending, error, refresh };
}

export function useSettingActions() {
  const { apiFetch } = useApi();

  function updateSetting(key: string, value: string, description?: string) {
    return apiFetch(`/settings/${key}`, {
      method: "PUT",
      body: JSON.stringify({ value, description }),
    });
  }

  return { updateSetting };
}
