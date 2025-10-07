import { act } from "@testing-library/react";
import useCategoryColorStore from "../store/categoryColorStore";
import { CATEGORY_COLORS } from "../constants/categoryColors";

describe("categoryColorStore", () => {
  beforeEach(() => {
    act(() => {
      useCategoryColorStore.getState().resetColors();
    });
    localStorage.clear();
  });

  it("should initialize with default colors", () => {
    const { colors } = useCategoryColorStore.getState();
    expect(colors).toEqual(CATEGORY_COLORS);
  });

  it("should set a color for a category", () => {
    act(() => {
      useCategoryColorStore.getState().setColor("Test Category", "#ff0000");
    });
    const { colors } = useCategoryColorStore.getState();
    expect(colors["Test Category"]).toBe("#ff0000");
  });

  it("should reset colors to default", () => {
    act(() => {
      useCategoryColorStore.getState().setColor("Test Category", "#ff0000");
      useCategoryColorStore.getState().resetColors();
    });
    const { colors } = useCategoryColorStore.getState();
    expect(colors).toEqual(CATEGORY_COLORS);
  });
});