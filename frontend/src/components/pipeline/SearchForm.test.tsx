import { render, screen, waitFor } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import SearchForm from "./SearchForm";

const mockMutate = vi.fn();

vi.mock("@/api/endpoints/pipeline/pipeline", () => ({
  usePipelineSearchPipelineSearchPost: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
}));

function renderForm(onJobStarted = vi.fn()) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <SearchForm onJobStarted={onJobStarted} />
    </QueryClientProvider>,
  );
}

describe("SearchForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all fields with defaults", () => {
    renderForm();

    expect(screen.getByLabelText(/location/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/query/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/types/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/limit/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/grid size/i)).toBeInTheDocument();
    expect(screen.getByText(/min score/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /start search/i }),
    ).toBeInTheDocument();
  });

  it("validates required fields", async () => {
    const user = userEvent.setup();
    renderForm();

    await user.click(screen.getByRole("button", { name: /start search/i }));

    await waitFor(() => {
      expect(screen.getByText(/location is required/i)).toBeInTheDocument();
      expect(screen.getByText(/query is required/i)).toBeInTheDocument();
    });

    expect(mockMutate).not.toHaveBeenCalled();
  });

  it("submits with valid data", async () => {
    const user = userEvent.setup();
    const onJobStarted = vi.fn();
    renderForm(onJobStarted);

    await user.type(screen.getByLabelText(/location/i), "Milano");
    await user.type(screen.getByLabelText(/query/i), "ristorante");
    await user.click(screen.getByRole("button", { name: /start search/i }));

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledTimes(1);
    });

    // Check the data passed to mutate
    const call = mockMutate.mock.calls[0];
    expect(call[0].data.location).toBe("Milano");
    expect(call[0].data.query).toBe("ristorante");
  });

  it("calls onJobStarted on success", async () => {
    const user = userEvent.setup();
    const onJobStarted = vi.fn();

    mockMutate.mockImplementation(
      (_data: unknown, opts: { onSuccess: (r: { data: { job_id: string } }) => void }) => {
        opts.onSuccess({ data: { job_id: "test-job-id" } });
      },
    );

    renderForm(onJobStarted);

    await user.type(screen.getByLabelText(/location/i), "Roma");
    await user.type(screen.getByLabelText(/query/i), "bar");
    await user.click(screen.getByRole("button", { name: /start search/i }));

    await waitFor(() => {
      expect(onJobStarted).toHaveBeenCalledWith("test-job-id");
    });
  });
});
