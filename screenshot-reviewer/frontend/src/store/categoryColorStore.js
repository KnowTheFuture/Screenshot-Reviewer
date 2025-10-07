import { create } from "zustand";
import { persist } from "zustand/middleware";

import { CATEGORY_COLORS } from "../constants/categoryColors";

const categoryColorStore = (set) => ({
  colors: { ...CATEGORY_COLORS },
  setColor: (category, color) =>
    set((state) => ({
      colors: { ...state.colors, [category]: color },
    })),
  resetColors: () => set({ colors: { ...CATEGORY_COLORS } }),
});

const useCategoryColorStore = create(
  persist(categoryColorStore, {
    name: "category-colors",
  })
);

export default useCategoryColorStore;