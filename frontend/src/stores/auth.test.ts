import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "./auth";

describe("useAuthStore", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({ apiKey: null });
  });

  it("starts with null when localStorage is empty", () => {
    expect(useAuthStore.getState().apiKey).toBeNull();
  });

  it("setApiKey stores in state and localStorage", () => {
    useAuthStore.getState().setApiKey("test-key-123");

    expect(useAuthStore.getState().apiKey).toBe("test-key-123");
    expect(localStorage.getItem("webseed-api-key")).toBe("test-key-123");
  });

  it("clearApiKey removes from state and localStorage", () => {
    useAuthStore.getState().setApiKey("test-key-123");
    useAuthStore.getState().clearApiKey();

    expect(useAuthStore.getState().apiKey).toBeNull();
    expect(localStorage.getItem("webseed-api-key")).toBeNull();
  });

  it("persists across store reads", () => {
    useAuthStore.getState().setApiKey("persistent-key");

    // Simulate reading from a fresh component
    const key = useAuthStore.getState().apiKey;
    expect(key).toBe("persistent-key");
  });
});
