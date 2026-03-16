import { create } from "zustand";

const STORAGE_KEY = "webseed-api-key";

interface AuthState {
  apiKey: string | null;
  setApiKey: (key: string) => void;
  clearApiKey: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  apiKey: localStorage.getItem(STORAGE_KEY),

  setApiKey: (key: string) => {
    localStorage.setItem(STORAGE_KEY, key);
    set({ apiKey: key });
  },

  clearApiKey: () => {
    localStorage.removeItem(STORAGE_KEY);
    set({ apiKey: null });
  },
}));
