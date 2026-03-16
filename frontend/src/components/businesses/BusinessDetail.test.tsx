import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";
import BusinessDetail from "./BusinessDetail";

const mockStatusMutate = vi.fn();
const mockBlacklistAddMutate = vi.fn();
const mockBlacklistRemoveMutate = vi.fn();
const mockDeleteMutate = vi.fn();

vi.mock("@/api/endpoints/businesses/businesses", () => ({
  useUpdateStatusBusinessesPlaceIdStatusPatch: () => ({
    mutate: mockStatusMutate,
    isPending: false,
  }),
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

const mockBusiness = {
  place_id: "ChIJ123",
  name: "Ristorante Roma",
  address: "Via Roma 1",
  city: "Roma",
  phone: "+39 123456",
  rating: 4.5,
  lead_score: 72,
  status: "searched",
};

function renderDetail(
  business = mockBusiness,
  onRefresh = vi.fn(),
) {
  return render(
    <MemoryRouter>
      <BusinessDetail business={business} onRefresh={onRefresh} />
    </MemoryRouter>,
  );
}

describe("BusinessDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all business fields", () => {
    renderDetail();

    expect(screen.getAllByText("Ristorante Roma")).toHaveLength(2);
    expect(screen.getByText("Via Roma 1")).toBeInTheDocument();
    expect(screen.getByText("+39 123456")).toBeInTheDocument();
    expect(screen.getByText("4.5")).toBeInTheDocument();
    expect(screen.getByText("72")).toBeInTheDocument();
    // "searched" appears in badge + select dropdown
    expect(screen.getAllByText("searched").length).toBeGreaterThanOrEqual(1);
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
});
