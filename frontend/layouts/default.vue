<script setup lang="ts">
const auth = useAuthStore();
const ws = useWebSocketStore();
const config = useRuntimeConfig();

onMounted(() => {
  if (auth.apiKey) {
    ws.connect(auth.apiKey, config.public.wsUrl as string);
  }
});
</script>

<template>
  <div class="flex h-screen">
    <LayoutSidebar />
    <div class="flex flex-1 flex-col overflow-hidden">
      <main class="flex-1 overflow-auto p-6">
        <slot />
      </main>
      <LayoutBottomPanel />
    </div>
  </div>
</template>
