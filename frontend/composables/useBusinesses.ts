import type {
  BusinessSummary,
  BusinessDetail,
  StatsResponse,
} from "~/types";
import { ApiError } from "~/composables/useApi";

export function useBusinessList(statusFilter?: Ref<string | undefined>) {
  const { apiFetch } = useApi();

  const businesses = ref<BusinessSummary[]>([]);
  const stats = ref<StatsResponse>({});
  const pending = ref(false);
  const error = ref<Error | null>(null);

  async function refresh() {
    pending.value = true;
    error.value = null;
    try {
      const statusParam = statusFilter?.value;
      const query = statusParam ? `?status=${statusParam}` : "";

      const [bizData, statsData] = await Promise.all([
        apiFetch<BusinessSummary[]>(`/businesses${query}`),
        apiFetch<StatsResponse>("/businesses/stats"),
      ]);

      businesses.value = bizData;
      stats.value = statsData;
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e));
    } finally {
      pending.value = false;
    }
  }

  // Initial fetch
  refresh();

  // Refetch when filter changes
  if (statusFilter) {
    watch(statusFilter, () => refresh());
  }

  return { businesses, stats, pending, error, refresh };
}

export function useBusinessDetail(placeId: Ref<string>) {
  const { apiFetch } = useApi();

  const business = ref<BusinessDetail | null>(null);
  const pending = ref(false);
  const error = ref<Error | null>(null);

  async function refresh() {
    pending.value = true;
    error.value = null;
    try {
      business.value = await apiFetch<BusinessDetail>(
        `/businesses/${placeId.value}`,
      );
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e));
    } finally {
      pending.value = false;
    }
  }

  refresh();

  watch(placeId, () => refresh());

  return { business, pending, error, refresh };
}

export function useBusinessActions() {
  const { apiFetch } = useApi();
  const config = useRuntimeConfig();
  const auth = useAuthStore();

  function patchStatus(placeId: string, to: string) {
    return apiFetch(`/businesses/${placeId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ to }),
    });
  }

  function blacklistAdd(placeId: string) {
    return apiFetch(`/businesses/${placeId}/blacklist`, { method: "POST" });
  }

  function blacklistRemove(placeId: string) {
    return apiFetch(`/businesses/${placeId}/blacklist`, { method: "DELETE" });
  }

  function deleteBusiness(placeId: string) {
    return apiFetch(`/businesses/${placeId}`, { method: "DELETE" });
  }

  function hardDelete(placeIds: string[]) {
    return apiFetch("/businesses/hard-delete", {
      method: "POST",
      body: JSON.stringify({ place_ids: placeIds }),
    });
  }

  async function exportCsv() {
    const base = config.public.apiBase as string;

    const response = await fetch(`${base}/businesses/export/csv`, {
      headers: auth.apiKey ? { "X-API-Key": auth.apiKey } : {},
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: response.statusText,
      }));
      throw new ApiError(
        response.status,
        errorData,
      );
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "businesses.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  function closeBusinesses(placeIds: string[]) {
    return apiFetch("/businesses/close", {
      method: "POST",
      body: JSON.stringify({ place_ids: placeIds }),
    });
  }

  return {
    patchStatus,
    blacklistAdd,
    blacklistRemove,
    deleteBusiness,
    hardDelete,
    closeBusinesses,
    exportCsv,
  };
}
