import { renderHook, act, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import useSelectionPersistence from "../hooks/useSelectionPersistence.js";
import useSelectionStore from "../store/selectionStore.js";

const STORAGE_KEY = "screenshot-selection";

describe("useSelectionPersistence", () => {
  beforeEach(() => {
    localStorage.clear();
    act(() => {
      useSelectionStore.getState().clear();
    });
  });

  afterEach(() => {
    vi.resetAllMocks();
    delete global.fetch;
    act(() => {
      useSelectionStore.getState().clear();
    });
  });

  it("restores selection from backend when available", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ selected: ["a", "b"] }),
    });
    global.fetch = fetchMock;

    renderHook(() => useSelectionPersistence());

    await waitFor(() => {
      expect(Array.from(useSelectionStore.getState().selected)).toEqual(["a", "b"]);
    });

    expect(fetchMock).toHaveBeenCalledWith("/api/state");
  });

  it("falls back to localStorage when backend fetch fails", async () => {
    const error = new Error("offline");
    const fetchMock = vi.fn().mockRejectedValue(error);
    global.fetch = fetchMock;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(["x"]));

    renderHook(() => useSelectionPersistence());

    await waitFor(() => {
      expect(Array.from(useSelectionStore.getState().selected)).toEqual(["x"]);
    });
  });

  it("persists selection updates to localStorage", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ selected: [] }),
    });
    global.fetch = fetchMock;

    renderHook(() => useSelectionPersistence());

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));

    act(() => {
      useSelectionStore.getState().setSelection(["one"]);
    });

    await waitFor(() => {
      expect(JSON.parse(localStorage.getItem(STORAGE_KEY))).toEqual(["one"]);
    });
  });

  it("clears persisted selection and notifies backend", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ selected: [] }) })
      .mockResolvedValue({ ok: true, json: async () => ({}) });
    global.fetch = fetchMock;

    const { result } = renderHook(() => useSelectionPersistence());

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));

    act(() => {
      useSelectionStore.getState().setSelection(["foo"]);
    });

    await waitFor(() => {
      expect(JSON.parse(localStorage.getItem(STORAGE_KEY))).toEqual(["foo"]);
    });

    act(() => {
      result.current.clearPersistence();
    });

    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    expect(Array.from(useSelectionStore.getState().selected)).toEqual([]);
    expect(fetchMock).toHaveBeenLastCalledWith("/api/state/clear", { method: "POST" });
  });
});
