import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";
import StatsCards from "./StatsCards";

vi.mock("@/api/endpoints/businesses/businesses", () => ({
  useGetStatsBusinessesStatsGet: () => ({
    data: {
      data: {
        searched: 5,
        enriched: 3,
        generated: 1,
        deployed: 2,
        emailed: 1,
        error_generate: 1,
        opted_out: 2,
      },
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
  it("renders computed stats from API data", () => {
    renderWithQuery(<StatsCards />);

    // Total: 5+3+1+2+1+1+2 = 15
    expect(screen.getByText("15")).toBeInTheDocument();
    // With sites: deployed(2) + emailed(1) = 3
    expect(screen.getByText("Total businesses")).toBeInTheDocument();
    expect(screen.getByText("With sites")).toBeInTheDocument();
    expect(screen.getByText("Errors")).toBeInTheDocument();
    expect(screen.getByText("Blacklisted")).toBeInTheDocument();
  });
});
