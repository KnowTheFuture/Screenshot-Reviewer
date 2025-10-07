import { create } from "zustand";
import { persist } from "zustand/middleware";

import DEFAULT_COLORS from "../constants/categoryColors.js";

const STORE_KEY = "category-colors";

const palette = Object.values(DEFAULT_COLORS);

const generateFallback = (categoryName) => {
  if (!palette.length) {
    return "#f1f3f5";
  }
  const index = Math.abs(categoryName?.length ?? 0) % palette.length;
  return palette[index];
};

const useCategoryColorStore = create(
  persist(
    (set, get) => ({
      colors: { ...DEFAULT_COLORS },
      setColor: (name, value) =>
        set((state) => ({
          colors: { ...state.colors, [name]: value },
        })),
      ensureColor: (name) => {
        if (!name) return;
        const state = get();
        if (!state.colors[name]) {
          const fallback = generateFallback(name);
          set({
            colors: { ...state.colors, [name]: fallback },
          });
        }
      },
      renameCategoryColor: (oldName, newName) => {
        if (!oldName || !newName) return;
        set((state) => {
          if (!state.colors[oldName]) {
            return state;
          }
          const next = { ...state.colors };
          const value = next[oldName];
          delete next[oldName];
          next[newName] = value;
          return { colors: next };
        });
      },
      removeColor: (name) =>
        set((state) => {
          if (!state.colors[name]) {
            return state;
          }
          const next = { ...state.colors };
          delete next[name];
          return { colors: next };
        }),
      resetColors: () => set({ colors: { ...DEFAULT_COLORS } }),
    }),
    {
      name: STORE_KEY,
      merge: (persisted, current) => ({
        ...current,
        ...persisted,
        colors: { ...DEFAULT_COLORS, ...(persisted?.colors ?? {}) },
      }),
    }
  )
);

export default useCategoryColorStore;
