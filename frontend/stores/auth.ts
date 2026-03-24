import { defineStore } from "pinia";

const STORAGE_KEY = "webseed-api-key";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    apiKey: null as string | null,
  }),

  actions: {
    init() {
      this.apiKey = localStorage.getItem(STORAGE_KEY);
    },

    setApiKey(key: string) {
      localStorage.setItem(STORAGE_KEY, key);
      this.apiKey = key;
    },

    clearApiKey() {
      localStorage.removeItem(STORAGE_KEY);
      this.apiKey = null;
    },
  },
});
