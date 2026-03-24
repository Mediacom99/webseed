export default defineNuxtRouteMiddleware((to) => {
  if (to.path === "/login") return;

  const auth = useAuthStore();
  // Ensure apiKey is loaded from localStorage before checking
  // (middleware runs before app.vue setup)
  if (!auth.apiKey) {
    auth.init();
  }
  if (!auth.apiKey) {
    return navigateTo("/login");
  }
});
