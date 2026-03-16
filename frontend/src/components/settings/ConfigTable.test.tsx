import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";
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
      <ConfigTable />
    </QueryClientProvider>,
  );
}

describe("ConfigTable", () => {
  it("renders config settings from mock data", () => {
    renderTable();

    expect(screen.getByText("config.contact_email")).toBeInTheDocument();
    expect(screen.getByText("config.sender_name")).toBeInTheDocument();
    expect(screen.getByText("Contact email")).toBeInTheDocument();
  });

  it("renders editable input fields", () => {
    renderTable();

    const inputs = screen.getAllByRole("textbox");
    expect(inputs.length).toBeGreaterThanOrEqual(2);
  });
});
