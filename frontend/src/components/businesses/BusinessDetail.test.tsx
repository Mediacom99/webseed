import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import BusinessDetail from "./BusinessDetail";

const mockBlacklistAddMutate = vi.fn();
const mockBlacklistRemoveMutate = vi.fn();
const mockDeleteMutate = vi.fn();

vi.mock("@/api/endpoints/businesses/businesses", () => ({
  useBlacklistAddBusinessesPlaceIdBlacklistPost: () => ({
    mutate: mockBlacklistAddMutate,
    isPending: false,
  }),
  useBlacklistRemoveBusinessesPlaceIdBlacklistDelete: () => ({
    mutate: mockBlacklistRemoveMutate,
    isPending: false,
  }),
  useDeleteBusinessBusinessesPlaceIdDelete: () => ({
    mutate: mockDeleteMutate,
    isPending: false,
  }),
}));

vi.mock("@/api/endpoints/pipeline/pipeline", () => ({
  usePipelineEnrichPipelineEnrichPost: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
  usePipelineGeneratePipelineGeneratePost: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
  usePipelineTestPipelineTestPost: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
  usePipelineDeployPipelineDeployPost: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
  usePipelineEmailPipelineEmailPost: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}));

const mockBusiness = {
  place_id: "ChIJ123",
  name: "Ristorante Roma",
  address: "Via Roma 1",
  phone: "+39 123456",
  rating: 4.5,
  reviews: 10,
  lead_score: 72,
  status: "searched",
  primary_type: "restaurant",
};

function renderDetail(
  business = mockBusiness,
  onRefresh = vi.fn(),
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <BusinessDetail business={business} onRefresh={onRefresh} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("BusinessDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders business header with name and status", () => {
    renderDetail();

    expect(screen.getByText("Ristorante Roma")).toBeInTheDocument();
    expect(screen.getByText("searched")).toBeInTheDocument();
    expect(screen.getByText("4.5")).toBeInTheDocument();
  });

  it("shows blacklist button", () => {
    renderDetail();
    expect(screen.getByText("Blacklist")).toBeInTheDocument();
  });

  it("shows unblacklist for opted_out business", () => {
    renderDetail({ ...mockBusiness, status: "opted_out" });
    expect(screen.getByText("Unblacklist")).toBeInTheDocument();
  });

  it("shows delete confirmation dialog", async () => {
    const user = userEvent.setup();
    renderDetail();

    await user.click(screen.getByText("Delete"));

    expect(screen.getByText("Delete business?")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("renders pipeline graph with 6 nodes", () => {
    renderDetail();

    expect(screen.getByText("Search")).toBeInTheDocument();
    // "Enrich" appears in both the graph and the action button
    expect(screen.getAllByText("Enrich").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Generate")).toBeInTheDocument();
    expect(screen.getByText("Test")).toBeInTheDocument();
    expect(screen.getByText("Deploy")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
  });

  it("shows next-step button for searched status", () => {
    renderDetail();
    expect(
      screen.getByRole("button", { name: "Enrich" }),
    ).toBeInTheDocument();
  });
});
