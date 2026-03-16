import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import RunPipelineForm from "./RunPipelineForm";

const mockRunMutate = vi.fn();
const mockEnrichMutate = vi.fn();

vi.mock("@/api/endpoints/businesses/businesses", () => ({
  useListBusinessesBusinessesGet: () => ({
    data: {
      data: [
        { place_id: "ChIJ1", name: "Ristorante Roma" },
        { place_id: "ChIJ2", name: "Bar Milano" },
      ],
      status: 200,
      headers: new Headers(),
    },
  }),
}));

vi.mock("@/api/endpoints/pipeline/pipeline", () => ({
  usePipelineRunPipelineRunPost: () => ({
    mutate: mockRunMutate,
    isPending: false,
  }),
  usePipelineEnrichPipelineEnrichPost: () => ({
    mutate: mockEnrichMutate,
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

function renderForm(onJobStarted = vi.fn()) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RunPipelineForm onJobStarted={onJobStarted} />
    </QueryClientProvider>,
  );
}

describe("RunPipelineForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders business list from API", () => {
    renderForm();

    expect(screen.getByText("Ristorante Roma")).toBeInTheDocument();
    expect(screen.getByText("Bar Milano")).toBeInTheDocument();
  });

  it("shows all step tabs", () => {
    renderForm();

    expect(screen.getByRole("tab", { name: "Full Run" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Enrich" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Generate" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Test" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Deploy" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Email" })).toBeInTheDocument();
  });

  it("disables submit when no businesses selected", () => {
    renderForm();

    const submitBtn = screen.getByRole("button", { name: /run pipeline/i });
    expect(submitBtn).toBeDisabled();
  });

  it("submits run with selected businesses", async () => {
    const user = userEvent.setup();
    renderForm();

    // Select first business
    const checkboxes = screen.getAllByRole("checkbox");
    await user.click(checkboxes[0]);

    const submitBtn = screen.getByRole("button", { name: /run pipeline \(1\)/i });
    expect(submitBtn).not.toBeDisabled();
    await user.click(submitBtn);

    expect(mockRunMutate).toHaveBeenCalledTimes(1);
    const call = mockRunMutate.mock.calls[0];
    expect(call[0].data.place_ids).toEqual(["ChIJ1"]);
  });
});
