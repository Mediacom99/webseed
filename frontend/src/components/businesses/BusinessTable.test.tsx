import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import BusinessTable from "./BusinessTable";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/api/endpoints/businesses/businesses", () => ({
  useHardDeleteBusinessesHardDeletePost: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
  useCloseBusinessesBusinessesClosePost: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
  useListBusinessesBusinessesGet: () => ({
    data: {
      data: [
        {
          place_id: "ChIJ1",
          name: "Ristorante Roma",
          status: "searched",
          city: "Roma",
          rating: 4.5,
          lead_score: 72,
        },
        {
          place_id: "ChIJ2",
          name: "Bar Milano",
          status: "enriched",
          city: "Milano",
          rating: 4.2,
          lead_score: 58,
        },
      ],
      status: 200,
      headers: new Headers(),
    },
    refetch: vi.fn(),
  }),
  useGetStatsBusinessesStatsGet: () => ({
    data: {
      data: { searched: 1, enriched: 1 },
      status: 200,
      headers: new Headers(),
    },
  }),
}));

function renderTable() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <BusinessTable />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("BusinessTable", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders rows from mock data", () => {
    renderTable();

    expect(screen.getByText("Ristorante Roma")).toBeInTheDocument();
    expect(screen.getByText("Bar Milano")).toBeInTheDocument();
    expect(screen.getByText("Roma")).toBeInTheDocument();
    expect(screen.getByText("Milano")).toBeInTheDocument();
  });

  it("shows status badges", () => {
    renderTable();

    expect(screen.getByText("searched")).toBeInTheDocument();
    expect(screen.getByText("enriched")).toBeInTheDocument();
  });

  it("row click navigates to detail page", async () => {
    const user = userEvent.setup();
    renderTable();

    await user.click(screen.getByText("Ristorante Roma"));

    expect(mockNavigate).toHaveBeenCalledWith("/businesses/ChIJ1");
  });

  it("displays rating and lead score values", () => {
    renderTable();

    expect(screen.getByText("4.5")).toBeInTheDocument();
    expect(screen.getByText("72")).toBeInTheDocument();
    expect(screen.getByText("4.2")).toBeInTheDocument();
    expect(screen.getByText("58")).toBeInTheDocument();
  });
});
