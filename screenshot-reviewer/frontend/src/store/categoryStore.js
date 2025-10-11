import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useCategoryStore = create(
    persist(
        (set) => ({
            items: [],
            setItems: (items) => set({ items: [...items] }),
            addLocal: (cat) => set((s) => ({ items: [...s.items, { ...cat }] })),
            renameLocal: (id, name) =>
                set((s) => ({ items: s.items.map((c) => (c.id === id ? { ...c, name } : c)) })),
            removeLocal: (id) => set((s) => ({ items: s.items.filter((c) => c.id !== id) })),
        }),
        {
            name: "categories-store",
            partialize: (s) => ({ items: s.items }),
            version: 1,
        }
    )
);