import clsx from "clsx";

function ScreenshotCard({ screenshot, isSelected, onToggle, onOpen }) {
  return (
    <div className="group relative">
      <button
        type="button"
        onClick={() => onToggle(screenshot.id)}
        className={clsx(
          "aspect-square w-full overflow-hidden rounded-xl border transition",
          isSelected
            ? "border-brand-500 ring-2 ring-brand-500"
            : "border-slate-200 hover:border-brand-200"
        )}
      >
        <img
          src={screenshot.thumbnail || screenshot.url || screenshot.path}
          alt={screenshot.summary || screenshot.path}
          className="h-full w-full object-cover"
        />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/40 via-transparent" />
        <div className="absolute left-2 top-2 flex items-center gap-2 text-xs text-white">
          {screenshot.primary_category && (
            <span className="rounded bg-black/40 px-2 py-1">
              {screenshot.primary_category}
            </span>
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
          <p className="text-[10px] opacity-60">Confidence {screenshot.confidence?.toFixed(2)}</p>
        </div>
      </button>
      <button
        type="button"
        onClick={() => onOpen(screenshot)}
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
  onToggle,
  onOpen,
  onSelectAll,
  page,
  totalPages,
  onPageChange,
}) {
  return (
    <section className="flex-1 overflow-auto bg-slate-50">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <button
            type="button"
            className="rounded border border-slate-200 px-3 py-1 hover:border-brand-400 hover:text-brand-600"
            onClick={onSelectAll}
          >
            Select page
          </button>
          <span>{selected.size} selected</span>
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
        {screenshots.map((screenshot) => (
          <ScreenshotCard
            key={`${screenshot.id}-${screenshot.filename || screenshot.path}`}
            screenshot={screenshot}
            isSelected={selected.has(screenshot.id)}
            onToggle={onToggle}
            onOpen={onOpen}
          />
        ))}
        {!screenshots.length && (
          <div className="col-span-full rounded-xl border border-dashed border-slate-200 bg-white p-12 text-center text-slate-400">
            No screenshots match the current filters.
          </div>
        )}
      </div>
    </section>
  );
}
