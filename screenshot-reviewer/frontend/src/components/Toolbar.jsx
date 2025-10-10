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
}) {
  return (
    <div className="toolbar-surface flex flex-wrap items-center justify-between gap-3 px-3 py-3">
      <div className="flex items-center gap-3">
        <select
          value={filter}
          onChange={(event) => onFilterChange?.(event.target.value)}
          className="rounded-lg border border-theme bg-[var(--surface-color)] px-3 py-2 text-sm text-theme shadow-sm focus:border-[var(--accent-color)] focus:outline-none"
        >
          <option value="all">All</option>
          <option value="pending">Pending</option>
          <option value="deferred">Deferred</option>
          <option value="low-confidence">Low confidence</option>
          <option value="re-review">Re-review</option>
        </select>
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-subtle">
          <button
            type="button"
            onClick={onGroupPrev}
            className="rounded-full border border-theme px-3 py-1 text-[10px] text-muted transition hover:border-[var(--accent-color)] hover:text-[var(--accent-color)]"
          >
            ◀ Prev
          </button>
          <span className="text-subtle">
            Group {currentGroup} / {totalGroups || 1}
          </span>
          <button
            type="button"
            onClick={onGroupNext}
            className="rounded-full border border-theme px-3 py-1 text-[10px] text-muted transition hover:border-[var(--accent-color)] hover:text-[var(--accent-color)]"
          >
            Next ▶
          </button>
        </div>
      </div>
      <div className="flex flex-1 justify-center px-3">
        <input
          value={search}
          onChange={(event) => onSearchChange?.(event.target.value)}
          className="w-full max-w-lg rounded-lg border border-theme bg-[var(--surface-muted)] px-4 py-2 text-sm text-theme shadow-inner focus:border-[var(--accent-color)] focus:bg-[var(--surface-color)] focus:outline-none"
          placeholder="Search by tag, summary, or OCR text"
        />
      </div>
      <div className="flex items-center gap-4 text-sm text-muted">
        <div className="flex items-center gap-1.5">
          <span className="text-subtle">Reviewed</span>
          <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs font-semibold text-[var(--accent-strong)]">
            {progress.reviewed}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-subtle">Deferred</span>
          <span className="rounded-full bg-[rgba(251,191,36,0.15)] px-2 py-0.5 text-xs font-semibold text-amber-600">
            {progress.deferred}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-subtle">Remaining</span>
          <span className="rounded-full bg-[rgba(148,163,184,0.18)] px-2 py-0.5 text-xs font-semibold text-theme">
            {progress.remaining}
          </span>
        </div>
      </div>
    </div>
  );
}
