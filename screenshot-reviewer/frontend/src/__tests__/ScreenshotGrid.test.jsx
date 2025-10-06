import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import ScreenshotGrid from "../components/ScreenshotGrid.jsx";

const buildScreenshots = (overrides = []) => {
  const base = Array.from({ length: 5 }, (_, index) => ({
    id: `id-${index}`,
    url: `/files/file-${index}.png`,
    path: `file-${index}.png`,
    summary: `Screenshot ${index}`,
  }));
  return base.map((item, index) => ({
    ...item,
    ...(overrides[index] ?? {}),
  }));
};

const getCardAt = (index) => document.querySelectorAll(".screenshot-card")[index];

const setup = (props = {}) => {
  const screenshots = props.screenshots ?? buildScreenshots();
  const onSelectionChange = props.onSelectionChange ?? vi.fn();
  const user = userEvent.setup();
  render(
    <ScreenshotGrid
      screenshots={screenshots}
      selected={props.selected}
      onSelectionChange={onSelectionChange}
      onOpen={() => {}}
      page={1}
      totalPages={1}
      onPageChange={() => {}}
    />
  );
  return { user, screenshots, onSelectionChange };
};

test("single click selects one card", async () => {
  const { user, onSelectionChange } = setup();
  await user.click(getCardAt(0));
  await waitFor(() => expect(getCardAt(0)).toHaveClass("selected"));
  await waitFor(() => expect(onSelectionChange).toHaveBeenLastCalledWith(["id-0"]));
});

test("ctrl/cmd click toggles selection", async () => {
  const { user, onSelectionChange } = setup();
  await user.click(getCardAt(1));
  await waitFor(() => expect(getCardAt(1)).toHaveClass("selected"));
  fireEvent.click(getCardAt(1), { ctrlKey: true });
  await waitFor(() => expect(getCardAt(1)).not.toHaveClass("selected"));
  expect(onSelectionChange).toHaveBeenCalledTimes(2);
});

test("shift click selects range", async () => {
  const { user, onSelectionChange } = setup();
  await user.click(getCardAt(1));
  await waitFor(() => expect(getCardAt(1)).toHaveClass("selected"));
  fireEvent.click(getCardAt(3), { shiftKey: true });
  await waitFor(() => {
    expect(getCardAt(1)).toHaveClass("selected");
    expect(getCardAt(2)).toHaveClass("selected");
    expect(getCardAt(3)).toHaveClass("selected");
  });
  await waitFor(() => expect(onSelectionChange).toHaveBeenLastCalledWith(["id-1", "id-2", "id-3"]));
});

test("placeholder renders when url missing", () => {
  const screenshots = buildScreenshots([{ url: null }]);
  setup({ screenshots });
  const placeholder = screen.getByText(/missing file/i);
  expect(placeholder).toBeInTheDocument();
  const img = screen.getByAltText("Screenshot 0");
  expect(img).toHaveAttribute("src", "/placeholder.png");
});

test("onSelectionChange receives array in selection order", async () => {
  const onSelectionChange = vi.fn();
  const { user } = setup({ onSelectionChange });
  await user.click(getCardAt(4));
  await waitFor(() => expect(onSelectionChange).toHaveBeenLastCalledWith(["id-4"]));
  fireEvent.click(getCardAt(0), { ctrlKey: true });
  await waitFor(() => expect(onSelectionChange).toHaveBeenLastCalledWith(["id-4", "id-0"]));
});
