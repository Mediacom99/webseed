import tailwindcss from "@tailwindcss/vite";

export default defineNuxtConfig({
  ssr: false,

  modules: ["@pinia/nuxt"],

  css: ["~/assets/css/main.css"],

  vite: {
    plugins: [tailwindcss()],
    server: {
      proxy: {
        "/api": {
          target: "http://localhost:8000",
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
        // WS proxy removed — connect directly to backend via runtimeConfig.public.wsUrl
      },
    },
  },

  runtimeConfig: {
    public: {
      apiBase: "/api",
      wsUrl: "ws://localhost:8000/ws",
    },
  },

  compatibilityDate: "2025-05-15",
});
