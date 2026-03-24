<script setup lang="ts">
const auth = useAuthStore();
auth.init();

const { toasts, dismiss } = useToast();
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>

  <!-- Toast container -->
  <div class="toast toast-end toast-bottom z-50">
    <TransitionGroup name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        :class="[
          'alert shadow-lg cursor-pointer',
          t.type === 'success' ? 'alert-success' : '',
          t.type === 'error' ? 'alert-error' : '',
          t.type === 'info' ? 'alert-info' : '',
        ]"
        @click="dismiss(t.id)"
      >
        <span>{{ t.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(30px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
