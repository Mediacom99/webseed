import { render, screen, waitFor } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import HealthCheckPage from "./HealthCheckPage";

const mockFetch = vi.fn();

vi.mock("@/api/client", () => ({
  customFetch: (...args: unknown[]) => mockFetch(...args),
  ApiError: class extends Error {
    status: number;
    data: unknown;
    constructor(status: number, data: unknown) {
      super(`API Error ${status}`);
      this.status = status;
      this.data = data;
    }
  },
}));

function getPreContent(): string | null {
  const pre = document.querySelector("pre");
  return pre?.textContent ?? null;
}

describe("HealthCheckPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders heading and description", () => {
    mockFetch.mockResolvedValue({ searched: 5, enriched: 3 });
    render(<HealthCheckPage />);

    expect(screen.getByText("webseed — Health Check")).toBeInTheDocument();
    expect(
      screen.getByText("API connectivity test via GET /api/businesses/stats"),
    ).toBeInTheDocument();
  });

  it("fetches and displays stats on mount", async () => {
    const mockStats = { searched: 5, enriched: 3, generated: 1 };
    mockFetch.mockResolvedValue(mockStats);

    render(<HealthCheckPage />);

    await waitFor(() => {
      expect(getPreContent()).toBe(JSON.stringify(mockStats, null, 2));
    });

    expect(mockFetch).toHaveBeenCalledWith("/businesses/stats", {
      method: "GET",
    });
  });

  it("displays error on API failure", async () => {
    mockFetch.mockRejectedValue(new Error("Network error"));

    render(<HealthCheckPage />);

    await waitFor(() => {
      expect(screen.getByText("Connection Error")).toBeInTheDocument();
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("refreshes data on button click", async () => {
    mockFetch
      .mockResolvedValueOnce({ searched: 1 })
      .mockResolvedValueOnce({ searched: 2 });

    render(<HealthCheckPage />);

    await waitFor(() => {
      expect(getPreContent()).toBe(JSON.stringify({ searched: 1 }, null, 2));
    });

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Refresh" }));

    await waitFor(() => {
      expect(getPreContent()).toBe(JSON.stringify({ searched: 2 }, null, 2));
    });

    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});
