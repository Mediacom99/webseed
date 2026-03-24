<script setup lang="ts">
import { ApiError } from "~/composables/useApi";

definePageMeta({ layout: "plain" });

const auth = useAuthStore();
const { apiFetch } = useApi();

const key = ref("");
const loading = ref(false);
const error = ref<string | null>(null);

async function handleSubmit() {
  if (!key.value.trim()) return;

  loading.value = true;
  error.value = null;

  // Temporarily store key so apiFetch can use it
  localStorage.setItem("webseed-api-key", key.value.trim());
  auth.apiKey = key.value.trim();

  try {
    await apiFetch("/businesses/stats", { method: "GET" });
    auth.setApiKey(key.value.trim());
    useToast().push("Authenticated successfully", "success");
    navigateTo("/search", { replace: true });
  } catch (err) {
    localStorage.removeItem("webseed-api-key");
    auth.apiKey = null;
    if (
      err instanceof ApiError &&
      (err.status === 401 || err.status === 403)
    ) {
      error.value = "Invalid API key";
    } else {
      error.value =
        err instanceof Error ? err.message : "Connection failed";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="card w-full max-w-sm bg-base-100 shadow-xl">
    <div class="card-body">
      <h2 class="card-title">webseed</h2>
      <p class="text-base-content/60">Enter your API key to continue</p>

      <form @submit.prevent="handleSubmit" class="mt-4 space-y-4">
        <div class="form-control">
          <label class="label" for="api-key">
            <span class="label-text">API Key</span>
          </label>
          <input
            id="api-key"
            v-model="key"
            type="password"
            placeholder="Enter your API key"
            class="input input-bordered w-full"
            autofocus
          />
        </div>

        <p v-if="error" class="text-sm text-error">{{ error }}</p>

        <button
          type="submit"
          class="btn btn-primary w-full"
          :disabled="loading || !key.trim()"
        >
          <span v-if="loading" class="loading loading-spinner loading-sm" />
          {{ loading ? "Validating..." : "Sign in" }}
        </button>
      </form>
    </div>
  </div>
</template>
