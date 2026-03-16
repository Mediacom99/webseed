import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";
import StatsCards from "./StatsCards";

vi.mock("@/api/endpoints/businesses/businesses", () => ({
  useGetStatsBusinessesStatsGet: () => ({
    data: {
      data: { searched: 5, enriched: 3, generated: 1 },
      status: 200,
      headers: new Headers(),
    },
    refetch: vi.fn(),
  }),
}));

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("StatsCards", () => {
  it("renders all status counts from API data", () => {
    renderWithQuery(<StatsCards />);

    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    // Status text appears in both card title and badge
    expect(screen.getAllByText("searched")).toHaveLength(2);
    expect(screen.getAllByText("enriched")).toHaveLength(2);
    expect(screen.getAllByText("generated")).toHaveLength(2);
  });
});
