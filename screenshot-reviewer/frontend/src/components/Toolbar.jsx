export default function Toolbar({
  filter,
  onFilterChange,
  search,
  onSearchChange,
  progress,
  onGroupPrev,
  onGroupNext,
  currentGroup,
  totalGroups,
  onOpenSettings,
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 border-b border-theme bg-[var(--surface-color)] px-6 py-4 text-theme">
      <div className="flex items-center gap-3">
        <select
          value={filter}
          onChange={(event) => onFilterChange?.(event.target.value)}
          className="rounded-md border border-theme px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
        >
          <option value="all">All</option>
          <option value="pending">Pending</option>
          <option value="deferred">Deferred</option>
          <option value="low-confidence">Low confidence</option>
          <option value="re-review">Re-review</option>
        </select>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onGroupPrev}
            className="rounded border border-theme px-2 py-1 text-xs text-theme/80 hover:border-brand-500 hover:text-brand-600"
          >
            Group ◀
          </button>
          <span className="text-xs text-theme/60">
            Group {currentGroup} / {totalGroups || 1}
          </span>
          <button
            type="button"
            onClick={onGroupNext}
            className="rounded border border-theme px-2 py-1 text-xs text-theme/80 hover:border-brand-500 hover:text-brand-600"
          >
            ▶
          </button>
        </div>
      </div>
      <div className="flex flex-1 justify-center px-4">
        <input
          value={search}
          onChange={(event) => onSearchChange?.(event.target.value)}
          className="w-full max-w-md rounded-md border border-theme px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          placeholder="Search by tag, summary, or OCR text"
        />
      </div>
      <div className="flex items-center gap-4 text-sm text-theme/80">
        <div className="flex items-center gap-2">
          <span className="text-theme/60">Reviewed</span>
          <span className="font-semibold text-brand-600">{progress.reviewed}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-theme/60">Deferred</span>
          <span className="font-semibold text-amber-500">{progress.deferred}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-theme/60">Remaining</span>
          <span className="font-semibold text-theme">{progress.remaining}</span>
        </div>
        <button
          type="button"
          onClick={onOpenSettings}
          className="rounded border border-theme px-3 py-1 text-xs text-theme hover:border-brand-500 hover:text-brand-600"
        >
          ⚙️ Settings
        </button>
      </div>
    </div>
  );
}
