import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import ConfigTable from "./ConfigTable";

vi.mock("@/api/endpoints/settings/settings", () => ({
  useListSettingsSettingsGet: () => ({
    data: {
      data: [
        {
          key: "config.contact_email",
          value: "test@example.com",
          description: "Contact email",
        },
        {
          key: "config.sender_name",
          value: "webseed",
          description: "Sender name",
        },
      ],
      status: 200,
      headers: new Headers(),
    },
  }),
  useUpdateSettingSettingsKeyPut: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}));

function renderTable() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <ConfigTable />
      </TooltipProvider>
    </QueryClientProvider>,
  );
}

describe("ConfigTable", () => {
  it("renders config settings with human-readable labels", () => {
    renderTable();

    // Human-readable labels (config. prefix stripped, underscores replaced)
    expect(screen.getByText("Contact Email")).toBeInTheDocument();
    expect(screen.getByText("Sender Name")).toBeInTheDocument();
  });

  it("renders editable input fields", () => {
    renderTable();

    const inputs = screen.getAllByRole("textbox");
    expect(inputs.length).toBeGreaterThanOrEqual(2);
  });
});
