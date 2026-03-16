import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { describe, it, expect, beforeEach } from "vitest";
import AuthGuard from "./AuthGuard";
import { useAuthStore } from "@/stores/auth";

function renderWithRoutes(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route element={<AuthGuard />}>
          <Route path="/" element={<div>Dashboard</div>} />
          <Route path="/settings" element={<div>Settings</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("AuthGuard", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({ apiKey: null });
  });

  it("redirects to /login when no API key", () => {
    renderWithRoutes("/");

    expect(screen.getByText("Login Page")).toBeInTheDocument();
    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
  });

  it("renders children when API key is present", () => {
    useAuthStore.setState({ apiKey: "test-key" });
    renderWithRoutes("/");

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.queryByText("Login Page")).not.toBeInTheDocument();
  });

  it("protects nested routes", () => {
    renderWithRoutes("/settings");

    expect(screen.getByText("Login Page")).toBeInTheDocument();
    expect(screen.queryByText("Settings")).not.toBeInTheDocument();
  });

  it("allows access to nested routes when authenticated", () => {
    useAuthStore.setState({ apiKey: "test-key" });
    renderWithRoutes("/settings");

    expect(screen.getByText("Settings")).toBeInTheDocument();
  });
});
