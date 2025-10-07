import { renderHook, act } from "@testing-library/react";
import useTheme from "../hooks/useTheme";
import themes from "../themes.json";

describe("useTheme", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("style");
    document.body.removeAttribute("data-theme");
  });

  it("should initialize with the default theme", () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("light");
  });

  it("should load the theme from localStorage", () => {
    localStorage.setItem("app-theme", "dark");
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("dark");
  });

  it("should change the theme", () => {
    const { result } = renderHook(() => useTheme());
    act(() => {
      result.current.setTheme("matrix");
    });
    expect(result.current.theme).toBe("matrix");
    expect(localStorage.getItem("app-theme")).toBe("matrix");
  });

  it("should apply theme variables to the document", () => {
    const { result } = renderHook(() => useTheme());
    act(() => {
      result.current.setTheme("dark");
    });
    const style = document.documentElement.style;
    expect(style.getPropertyValue("--bg-color")).toBe(themes.dark.background);
    expect(style.getPropertyValue("--text-color")).toBe(themes.dark.text);
  });
});