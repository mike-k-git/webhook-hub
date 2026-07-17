import { screen, render } from "@testing-library/react";
import { Badge } from "../components/Badge";

it("harness render and matches", () => {
  render(<Badge status="paused" />);

  expect(screen.getByText("paused")).toHaveClass("bg-amber-50");
});
