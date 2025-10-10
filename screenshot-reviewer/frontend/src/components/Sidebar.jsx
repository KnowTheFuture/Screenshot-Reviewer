import { useState } from "react";
import clsx from "clsx";

import { CATEGORY_COLORS } from "../constants/categoryColors.js";
import useCategoryColorStore from "../store/categoryColorStore.js";

const DEFAULT_PENDING_COLOR = "#F97316";

function CategoryItem({ category, isActive, onClick, color }) {
  const accentStyle = color ? { "--category-accent": color } : undefined;
  return (
    <button
      type="button"
      onClick={onClick}
      style={accentStyle}
      className={clsx(
        "flex w-full items-center justify-between rounded-xl px-3 py-2 text-left transition",
        isActive
          ? "bg-[var(--accent-soft)] text-theme shadow-sm"
          : "text-theme opacity-80 hover:bg-[var(--surface-muted)] hover:opacity-100"
      )}
    >
      <span className="flex items-center gap-2 font-medium tracking-tight">
        {color && <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />}
        {category.name}
      </span>
      <span
        className="category-count rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-subtle"
        data-color={color ? "true" : undefined}
      >
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
  const colors = useCategoryColorStore((state) => state.colors);
  const [showForm, setShowForm] = useState(false);
  const [newCategory, setNewCategory] = useState("");
  const [renameTarget, setRenameTarget] = useState(null);
  const [renameValue, setRenameValue] = useState("");
  const [renameOriginalName, setRenameOriginalName] = useState("");

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
    onRename?.(renameTarget, renameValue.trim(), renameOriginalName);
    setRenameValue("");
    setRenameTarget(null);
    setRenameOriginalName("");
  };

  return (
    <aside className="sidebar-panel flex h-full w-72 shrink-0 flex-col">
      <div className="flex items-center justify-between px-5 py-5">
        <h2 className="text-lg font-semibold text-theme tracking-tight">Categories</h2>
        <button
          type="button"
          className="rounded-full bg-[var(--accent-color)] px-4 py-1 text-sm font-semibold text-white shadow-sm transition hover:bg-[var(--accent-strong)]"
          onClick={() => setShowForm((prev) => !prev)}
        >
          {showForm ? "Cancel" : "Add"}
        </button>
      </div>
      <div className="scroll-soft flex-1 space-y-1 overflow-y-auto px-4 pb-6">
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
              color={colors[category.name] ?? CATEGORY_COLORS[category.name] ?? CATEGORY_COLORS.default}
            />
            <div className="category-actions flex gap-3 px-3 text-[11px] font-semibold uppercase tracking-wide">
              <button
                type="button"
                className="transition hover:text-[var(--accent-color)]"
                onClick={() => {
                  setRenameTarget(category.id);
                  setRenameValue(category.name);
                  setRenameOriginalName(category.name);
                }}
              >
                Rename
              </button>
              <button
                type="button"
                className="text-red-400 transition hover:text-red-500"
                onClick={() => onDelete?.(category.id, category.name)}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
      {showForm && (
        <form onSubmit={handleSubmit} className="border-t border-theme px-5 py-4">
          <label className="block text-sm font-semibold text-theme">
            New category
            <input
              value={newCategory}
              onChange={(event) => setNewCategory(event.target.value)}
              className="mt-1 w-full rounded border border-theme bg-[var(--surface-color)] px-3 py-2 text-sm text-theme shadow-sm focus:border-[var(--accent-color)] focus:outline-none"
              placeholder="e.g. Research"
            />
          </label>
          <div className="mt-4 flex justify-end gap-2">
            <button type="submit" className="rounded bg-[var(--accent-color)] px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-[var(--accent-strong)]">
              Save
            </button>
          </div>
        </form>
      )}
      {renameTarget && (
        <form onSubmit={handleRename} className="border-t border-theme px-5 py-4">
          <label className="block text-sm font-semibold text-theme">
            Rename category
            <input
              value={renameValue}
              onChange={(event) => setRenameValue(event.target.value)}
              className="mt-1 w-full rounded border border-theme bg-[var(--surface-color)] px-3 py-2 text-sm text-theme shadow-sm focus:border-[var(--accent-color)] focus:outline-none"
            />
          </label>
          <div className="mt-4 flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-subtle">
            <button
              type="button"
              onClick={() => {
                setRenameTarget(null);
                setRenameValue("");
                setRenameOriginalName("");
              }}
            >
              Cancel
            </button>
            <button type="submit" className="rounded bg-[var(--accent-color)] px-3 py-1.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[var(--accent-strong)]">
              Update
            </button>
          </div>
        </form>
      )}
    </aside>
  );
}
