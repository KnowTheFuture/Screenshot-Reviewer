import { renderHook, act } from "@testing-library/react";
import { useState } from "react";

import useSelectionPersistence from "../hooks/useSelectionPersistence.js";

describe("useSelectionPersistence", () => {
  beforeEach(() => localStorage.clear());

  it("restores selection from localStorage on mount", () => {
    localStorage.setItem("selection", JSON.stringify(["a", "b"]));

    const { result } = renderHook(() => {
      const [selected, setSelection] = useState(new Set());
      useSelectionPersistence(selected, setSelection);
      return selected;
    });

    expect(Array.from(result.current)).toEqual(["a", "b"]);
  });

  it("persists selection on beforeunload", () => {
    const { result } = renderHook(() => {
      const [selected, setSelection] = useState(new Set(["x", "y"]));
      useSelectionPersistence(selected, setSelection);
      return selected;
    });

    act(() => {
      window.dispatchEvent(new Event("beforeunload"));
    });

    expect(JSON.parse(localStorage.getItem("selection"))).toEqual(Array.from(result.current));
  });
});
