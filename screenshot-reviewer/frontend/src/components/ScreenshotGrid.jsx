import clsx from "clsx";
import { useMemo, useState } from "react";

import { CATEGORY_COLORS } from "../constants/categoryColors.js";
import useCategoryColorStore from "../store/categoryColorStore.js";

const normalizeSelection = (value) => {
  if (!value) return new Set();
  if (value instanceof Set) return new Set(value);
  if (Array.isArray(value)) return new Set(value);
  return new Set([value]);
};

function ScreenshotCard({ screenshot, isSelected, onClick, onOpen, tintStyle, categoryKey }) {
  const imageSrc = screenshot.thumbnail || screenshot.url || "/placeholder.png";
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick(event);
        }
      }}
      data-category={categoryKey || undefined}
      style={tintStyle}
      className={clsx(
        "screenshot-card group relative aspect-square w-full cursor-pointer overflow-hidden transition",
        {
          selected: isSelected,
          tinted: Boolean(tintStyle),
        }
      )}
    >
      <img
        src={imageSrc}
        alt={screenshot.summary || screenshot.path}
        className="h-full w-full object-cover"
      />
      {!screenshot.url && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-slate-900/30 text-xs font-medium text-white">
          Missing file
        </div>
      )}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/40 via-transparent" />
      <div className="absolute left-2 top-2 flex items-center gap-2 text-xs text-white">
        {screenshot.primary_category && (
          <span className="rounded bg-black/40 px-2 py-1">{screenshot.primary_category}</span>
        )}
        {screenshot.status === "re-review" && (
          <span className="rounded bg-amber-500 px-2 py-1">Re-review</span>
        )}
        {screenshot.status === "deleted" && (
          <span className="rounded bg-red-500 px-2 py-1">Deleted</span>
        )}
      </div>
      <div className="pointer-events-none absolute inset-x-0 bottom-0 p-2 text-left text-xs text-white">
        <p className="truncate font-medium">{screenshot.summary || screenshot.path}</p>
        <p className="text-[10px] opacity-60">
          Confidence {screenshot.confidence != null ? screenshot.confidence.toFixed(2) : "—"}
        </p>
      </div>
      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation();
          onOpen(screenshot);
        }}
        className="absolute right-2 top-2 hidden rounded-full bg-white/80 px-2 py-1 text-xs font-medium text-slate-700 shadow group-hover:block"
      >
        Details
      </button>
    </div>
  );
}

export default function ScreenshotGrid({
  screenshots,
  selected,
  onSelectionChange,
  onOpen,
  page,
  totalPages,
  onPageChange,
  categoryFilter = "all",
  gridColumns = 5,
  gridRows = 5,
  gridGap = 2,
  pageSize,
}) {
  const categoryColors = useCategoryColorStore((state) => state.colors);
  const isControlled = selected !== undefined;
  const [internalSelection, setInternalSelection] = useState(() => normalizeSelection(selected));
  const clampedColumns = Math.max(1, Math.min(10, gridColumns));
  const clampedRows = Math.max(1, Math.min(10, gridRows));
  const clampedGap = Math.max(0, Math.min(32, gridGap));
  const maxItems = pageSize ?? clampedColumns * clampedRows;
  const items = useMemo(() => screenshots.slice(0, Math.max(1, maxItems)), [screenshots, maxItems]);

  const selectionSet = useMemo(
    () => (isControlled ? normalizeSelection(selected) : internalSelection),
    [isControlled, internalSelection, selected]
  );

  const emitSelection = (next) => {
    const normalized = normalizeSelection(next);
    if (!isControlled) {
      setInternalSelection(normalized);
    }
    onSelectionChange?.(Array.from(normalized));
  };

  const toggleSelection = (screenshotId) => {
    const copy = new Set(selectionSet);
    if (copy.has(screenshotId)) copy.delete(screenshotId);
    else copy.add(screenshotId);
    emitSelection(copy);
  };

  const selectRange = (anchorIndex, targetIndex) => {
    const [start, end] =
      anchorIndex < targetIndex ? [anchorIndex, targetIndex] : [targetIndex, anchorIndex];
    const idsInRange = items.slice(start, end + 1).map((item) => item.id);
    emitSelection(idsInRange);
  };

  const handleClick = (event, screenshotId, index) => {
    if (event.metaKey || event.ctrlKey) {
      toggleSelection(screenshotId);
      return;
    }

    if (event.shiftKey && selectionSet.size) {
      const ids = items.map((item) => item.id);
      const selectedIndices = ids
        .map((id, idx) => (selectionSet.has(id) ? idx : -1))
        .filter((idx) => idx >= 0);
      const anchorIndex = selectedIndices.length
        ? selectedIndices[selectedIndices.length - 1]
        : index;
      selectRange(anchorIndex, index);
      return;
    }

    emitSelection([screenshotId]);
  };

  const selectEntirePage = () => {
    emitSelection(items.map((item) => item.id));
  };

  return (
    <section className="grid-surface scroll-soft flex-1 overflow-auto">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 text-sm text-muted">
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="rounded-full border border-theme px-3 py-1 text-xs font-semibold uppercase tracking-wide text-muted transition hover:border-[var(--accent-color)] hover:text-[var(--accent-color)]"
            onClick={selectEntirePage}
          >
            Select page
          </button>
          <span>{selectionSet.size} selected</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => onPageChange?.(page - 1)}
            className="rounded border border-theme px-3 py-1 text-xs font-semibold uppercase tracking-wide transition hover:border-[var(--accent-color)] hover:text-[var(--accent-color)] disabled:cursor-not-allowed disabled:opacity-40"
          >
            Prev
          </button>
          <span>
            Page {page} / {totalPages || 1}
          </span>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => onPageChange?.(page + 1)}
            className="rounded border border-theme px-3 py-1 text-xs font-semibold uppercase tracking-wide transition hover:border-[var(--accent-color)] hover:text-[var(--accent-color)] disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
      <div
        className="grid px-4 pb-6"
        style={{
          gridTemplateColumns: `repeat(${clampedColumns}, minmax(0, 1fr))`,
          gap: `${clampedGap}px`,
        }}
      >
        {items.map((screenshot, index) => {
          const categoryKey = screenshot.primary_category ?? screenshot.category ?? "default";
          const categoryColor =
            categoryColors[categoryKey] ??
            CATEGORY_COLORS[categoryKey] ??
            CATEGORY_COLORS.default;
          const tintStyle =
            categoryFilter === "all"
              ? { "--category-color": categoryColor }
              : undefined;

          return (
            <ScreenshotCard
              key={screenshot.id}
              screenshot={screenshot}
              isSelected={selectionSet.has(screenshot.id)}
              onClick={(event) => handleClick(event, screenshot.id, index)}
              onOpen={onOpen}
              tintStyle={tintStyle}
              categoryKey={categoryFilter === "all" ? categoryKey : undefined}
            />
          );
        })}
      </div>
    </section>
  );
}
