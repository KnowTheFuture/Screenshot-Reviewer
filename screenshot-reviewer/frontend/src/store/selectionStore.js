import { create } from "zustand";

export const useSelectionStore = create((set, get) => ({
  selected: new Set(),
  page: 1,
  pageSize: 50,
  total: 0,
  goToNext: () => {
    set((state) => ({ page: state.page + 1 }));
  },
  goToPrev: () => {
    set((state) => ({ page: Math.max(1, state.page - 1) }));
  },
  setPage: (page) => set({ page }),
  setTotal: (total) => set({ total }),
  toggle: (id) => {
    const copy = new Set(get().selected);
    if (copy.has(id)) {
      copy.delete(id);
    } else {
      copy.add(id);
    }
    set({ selected: copy });
  },
  clear: () => set({ selected: new Set() }),
  setSelection: (ids) => set({ selected: new Set(ids) }),
  triggerSave: () => {
    // placeholder, replaced at runtime by components needing CMD+S
  },
  setTriggerSave: (callback) => set({ triggerSave: callback }),
}));

export default useSelectionStore;
