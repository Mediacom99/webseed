import { render, screen, waitFor } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import LoginPage from "./LoginPage";
import { useAuthStore } from "@/stores/auth";

const mockFetch = vi.fn();
const mockNavigate = vi.fn();

vi.mock("@/api/client", () => ({
  customFetch: (...args: unknown[]) => mockFetch(...args),
  ApiError: class extends Error {
    status: number;
    data: unknown;
    constructor(status: number, data: unknown) {
      super(`API Error ${status}`);
      this.name = "ApiError";
      this.status = status;
      this.data = data;
    }
  },
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <LoginPage />
    </MemoryRouter>,
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    useAuthStore.setState({ apiKey: null });
  });

  it("renders login form", () => {
    renderLogin();

    expect(screen.getByText("webseed")).toBeInTheDocument();
    expect(screen.getByLabelText("API Key")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
  });

  it("submit button is disabled when input is empty", () => {
    renderLogin();

    expect(screen.getByRole("button", { name: "Sign in" })).toBeDisabled();
  });

  it("redirects on valid key", async () => {
    mockFetch.mockResolvedValue({ searched: 0 });
    const user = userEvent.setup();

    renderLogin();

    await user.type(screen.getByLabelText("API Key"), "valid-key");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/", { replace: true });
    });

    expect(useAuthStore.getState().apiKey).toBe("valid-key");
  });

  it("shows error on invalid key (401)", async () => {
    const { ApiError } = await import("@/api/client");
    mockFetch.mockRejectedValue(new ApiError(401, { detail: "Unauthorized" }));
    const user = userEvent.setup();

    renderLogin();

    await user.type(screen.getByLabelText("API Key"), "bad-key");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByText("Invalid API key")).toBeInTheDocument();
    });

    // Key should not be stored
    expect(useAuthStore.getState().apiKey).toBeNull();
  });
});
