import { useState } from "react";
import clsx from "clsx";

import { CATEGORY_COLORS } from "../constants/categoryColors.js";

const DEFAULT_PENDING_COLOR = "#F97316";

function CategoryItem({ category, isActive, onClick, color }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        "flex w-full items-center justify-between rounded-lg px-3 py-2 text-left transition",
        isActive ? "bg-[var(--surface-color)]/80 text-theme" : "text-theme/70 hover:bg-[var(--surface-color)]/60"
      )}
    >
      <span className="flex items-center gap-2 font-medium">
        {color && <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />}
        {category.name}
      </span>
      <span className="rounded bg-[var(--border-color)]/40 px-2 py-0.5 text-xs text-theme/70">
        {category.count}
      </span>
    </button>
  );
}

export default function Sidebar({
  categories,
  activeCategory,
  onSelect,
  onCreate,
  onDelete,
  onRename,
}) {
  const [showForm, setShowForm] = useState(false);
  const [newCategory, setNewCategory] = useState("");
  const [renameTarget, setRenameTarget] = useState(null);
  const [renameValue, setRenameValue] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!newCategory.trim()) return;
    onCreate?.(newCategory.trim());
    setNewCategory("");
    setShowForm(false);
  };

  const handleRename = (event) => {
    event.preventDefault();
    if (!renameTarget || !renameValue.trim()) return;
    onRename?.(renameTarget, renameValue.trim());
    setRenameValue("");
    setRenameTarget(null);
  };

  return (
    <aside className="settings-surface flex h-full w-64 flex-col border-r border-theme">
      <div className="flex items-center justify-between px-4 py-4">
        <h2 className="text-lg font-semibold text-theme">Categories</h2>
        <button
          type="button"
          className="rounded-full bg-brand-500 px-3 py-1 text-sm font-medium text-white hover:bg-brand-600"
          onClick={() => setShowForm((prev) => !prev)}
        >
          {showForm ? "Cancel" : "Add"}
        </button>
      </div>
      <div className="flex-1 space-y-1 overflow-y-auto px-3 pb-4">
        <CategoryItem
          key="all"
          category={{ name: "All", count: categories.reduce((acc, c) => acc + c.count, 0) }}
          isActive={activeCategory === "all"}
          onClick={() => onSelect?.("all")}
        color="var(--highlight-color)"
      />
      <CategoryItem
        key="pending"
        category={{ name: "Pending", count: categories.reduce((acc, c) => acc + c.pending, 0) }}
        isActive={activeCategory === "pending"}
        onClick={() => onSelect?.("pending")}
        color={DEFAULT_PENDING_COLOR}
      />
      {categories.map((category) => (
          <div key={category.id} className="space-y-1">
            <CategoryItem
              category={{ name: category.name, count: category.count }}
              isActive={activeCategory === category.id}
              onClick={() => onSelect?.(category.id)}
              color={CATEGORY_COLORS[category.name]}
            />
            <div className="flex gap-2 px-2 text-theme/60">
              <button
                type="button"
                className="text-xs hover:text-brand-500"
                onClick={() => {
                  setRenameTarget(category.id);
                  setRenameValue(category.name);
                }}
              >
                Rename
              </button>
              <button
                type="button"
                className="text-xs text-red-400 hover:text-red-500"
                onClick={() => onDelete?.(category.id)}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
      {showForm && (
        <form onSubmit={handleSubmit} className="border-t border-theme px-4 py-3">
          <label className="block text-sm font-medium text-theme">
            New category
            <input
              value={newCategory}
              onChange={(event) => setNewCategory(event.target.value)}
              className="mt-1 w-full rounded border border-theme px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              placeholder="e.g. Research"
            />
          </label>
          <div className="mt-3 flex justify-end gap-2">
            <button type="submit" className="rounded bg-brand-500 px-3 py-1.5 text-sm text-white">
              Save
            </button>
          </div>
        </form>
      )}
      {renameTarget && (
        <form onSubmit={handleRename} className="border-t border-theme px-4 py-3">
          <label className="block text-sm font-medium text-theme">
            Rename category
            <input
              value={renameValue}
              onChange={(event) => setRenameValue(event.target.value)}
              className="mt-1 w-full rounded border border-theme px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            />
          </label>
          <div className="mt-3 flex justify-between text-xs text-theme/60">
            <button
              type="button"
              onClick={() => {
                setRenameTarget(null);
                setRenameValue("");
              }}
            >
              Cancel
            </button>
            <button type="submit" className="rounded bg-brand-500 px-3 py-1.5 text-sm text-white">
              Update
            </button>
          </div>
        </form>
      )}
    </aside>
  );
}
