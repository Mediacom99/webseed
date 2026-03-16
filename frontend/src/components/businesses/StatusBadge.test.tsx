import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import StatusBadge from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders status text with underscores replaced by spaces", () => {
    render(<StatusBadge status="email_queued" />);
    expect(screen.getByText("email queued")).toBeInTheDocument();
  });

  it("renders simple status", () => {
    render(<StatusBadge status="searched" />);
    expect(screen.getByText("searched")).toBeInTheDocument();
  });

  it("renders error status", () => {
    render(<StatusBadge status="error_deploy" />);
    expect(screen.getByText("error deploy")).toBeInTheDocument();
  });
});
