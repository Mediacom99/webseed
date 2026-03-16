import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, beforeEach } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import Sidebar from "./Sidebar";
import { useAuthStore } from "@/stores/auth";

function renderSidebar() {
  return render(
    <MemoryRouter>
      <TooltipProvider>
        <Sidebar />
      </TooltipProvider>
    </MemoryRouter>,
  );
}

describe("Sidebar", () => {
  beforeEach(() => {
    useAuthStore.setState({ apiKey: "test-key" });
  });

  it("renders all nav items", () => {
    renderSidebar();

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Search")).toBeInTheDocument();
    expect(screen.getByText("Businesses")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("renders app name", () => {
    renderSidebar();

    expect(screen.getByText("webseed")).toBeInTheDocument();
  });

  it("collapses sidebar on toggle click", async () => {
    const user = userEvent.setup();
    renderSidebar();

    const collapseButton = screen.getByLabelText("Collapse sidebar");
    await user.click(collapseButton);

    // Nav labels should be hidden when collapsed
    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
    expect(screen.queryByText("Search")).not.toBeInTheDocument();
  });

  it("expands sidebar on toggle click when collapsed", async () => {
    const user = userEvent.setup();
    renderSidebar();

    // Collapse
    await user.click(screen.getByLabelText("Collapse sidebar"));
    // Expand
    await user.click(screen.getByLabelText("Expand sidebar"));

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });
});
