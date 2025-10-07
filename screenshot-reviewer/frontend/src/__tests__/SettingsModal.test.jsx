import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import axios from "axios";

import SettingsModal from "../components/SettingsModal.jsx";

vi.mock("axios");

const BASE_SETTINGS = Object.freeze({
  highlightColor: "#FFD700",
});

describe("SettingsModal", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    localStorage.clear();
  });

  it("updates highlight color and persists to localStorage", () => {
    let settings = { ...BASE_SETTINGS };
    const handleChange = vi.fn((update) => {
      settings = { ...settings, ...update };
      localStorage.setItem("appSettings", JSON.stringify(settings));
    });

    render(
      <SettingsModal
        isOpen
        onClose={() => {}}
        settings={settings}
        onChangeSettings={handleChange}
        categories={[]}
      />
    );

    const input = screen.getByLabelText(/Selection highlight/i);
    fireEvent.change(input, { target: { value: "#00ff00" } });

    expect(handleChange).toHaveBeenCalledWith({ highlightColor: "#00ff00" });
  });

  it("clears selection locally and remotely", async () => {
    axios.post.mockResolvedValue({ data: { status: "cleared" } });
    localStorage.setItem("selection", JSON.stringify(["foo"]));

    render(
      <SettingsModal
        isOpen
        onClose={() => {}}
        settings={{ ...BASE_SETTINGS }}
        onChangeSettings={() => {}}
        categories={[]}
      />
    );

    fireEvent.click(screen.getByText(/Clear saved selection/i));

    await waitFor(() => expect(axios.post).toHaveBeenCalledWith("/api/state/clear"));
    expect(localStorage.getItem("selection")).toBeNull();
  });
});
