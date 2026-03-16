import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi } from "vitest";
import PromptEditor from "./PromptEditor";

vi.mock("@/api/endpoints/settings/settings", () => ({
  useListSettingsSettingsGet: () => ({
    data: {
      data: [
        {
          key: "prompt.site_gen",
          value: "Generate a site for {name}",
          description: "Site generation prompt",
        },
        {
          key: "prompt.email_gen",
          value: "Write an email for {name}",
          description: "Email prompt",
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

function renderEditor() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <PromptEditor />
    </QueryClientProvider>,
  );
}

describe("PromptEditor", () => {
  it("renders grouped prompt settings", () => {
    renderEditor();

    expect(screen.getByText("Site Generation")).toBeInTheDocument();
    expect(screen.getByText("Email Generation")).toBeInTheDocument();
    expect(screen.getByText("prompt.site_gen")).toBeInTheDocument();
    expect(screen.getByText("prompt.email_gen")).toBeInTheDocument();
  });
});
