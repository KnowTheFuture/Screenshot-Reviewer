import clsx from "clsx";
import { useMemo, useState } from "react";

const normalizeSelection = (value) => {
  if (!value) return new Set();
  if (value instanceof Set) return new Set(value);
  if (Array.isArray(value)) return new Set(value);
  return new Set([value]);
};

function ScreenshotCard({ screenshot, isSelected, onClick, onOpen }) {
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
      className={clsx(
        "screenshot-card group relative aspect-square w-full cursor-pointer overflow-hidden rounded-xl border transition",
        { selected: isSelected }
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
}) {
  const isControlled = selected !== undefined;
  const [internalSelection, setInternalSelection] = useState(() => normalizeSelection(selected));

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
    const idsInRange = screenshots.slice(start, end + 1).map((item) => item.id);
    emitSelection(idsInRange);
  };

  const handleClick = (event, screenshotId, index) => {
    if (event.metaKey || event.ctrlKey) {
      toggleSelection(screenshotId);
      return;
    }

    if (event.shiftKey && selectionSet.size) {
      const ids = screenshots.map((item) => item.id);
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
    emitSelection(screenshots.map((item) => item.id));
  };

  return (
    <section className="flex-1 overflow-auto bg-slate-50">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <button
            type="button"
            className="rounded border border-slate-200 px-3 py-1 hover:border-brand-400 hover:text-brand-600"
            onClick={selectEntirePage}
          >
            Select page
          </button>
          <span>{selectionSet.size} selected</span>
        </div>
        <div className="flex items-center gap-3 text-sm text-slate-500">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => onPageChange?.(page - 1)}
            className="rounded border border-slate-200 px-3 py-1 disabled:opacity-40"
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
            className="rounded border border-slate-200 px-3 py-1 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 px-6 pb-8 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {screenshots.map((screenshot, index) => (
          <ScreenshotCard
            key={screenshot.id}
            screenshot={screenshot}
            isSelected={selectionSet.has(screenshot.id)}
            onClick={(event) => handleClick(event, screenshot.id, index)}
            onOpen={onOpen}
          />
        ))}
      </div>
    </section>
  );
}
