<script setup lang="ts">
import { AlertCircle } from "lucide-vue-next";

const props = defineProps<{
  error: {
    statusCode?: number;
    message?: string;
  };
}>();

function handleRetry() {
  clearError({ redirect: "/" });
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-base-200 p-4">
    <div class="card w-full max-w-md bg-base-100 shadow-xl">
      <div class="card-body items-center text-center">
        <AlertCircle class="h-12 w-12 text-error" />
        <h2 class="card-title mt-4">Something went wrong</h2>
        <p class="text-base-content/60">
          {{ error.message ?? "An unexpected error occurred" }}
        </p>
        <div class="card-actions mt-4">
          <button class="btn btn-primary" @click="handleRetry">
            Try again
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
