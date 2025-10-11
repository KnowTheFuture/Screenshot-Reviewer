import { useState } from "react";

export default function LexiconPanel({ entries, onCreate, onDelete, onOpenSettings }) {
  const [keyword, setKeyword] = useState("");
  const [tags, setTags] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!keyword.trim() || !tags.trim()) return;
    onCreate?.({
      keyword: keyword.trim(),
      tags: tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
    });
    setKeyword("");
    setTags("");
  };

  return (
    <aside className="lexicon-panel flex w-48 shrink-0 flex-col">
      <div className="flex items-start justify-between px-4 py-4">
        <div>
          <h2 className="text-lg font-semibold text-theme">Lexicon</h2>
          <p className="text-xs uppercase tracking-wide text-subtle">Keywords that auto-suggest tags.</p>
        </div>
        <button
          type="button"
          className="rounded-full border border-theme px-3 py-1 text-xs font-semibold text-muted transition hover:bg-[var(--surface-muted)] disabled:cursor-not-allowed disabled:opacity-40"
          onClick={() => onOpenSettings?.()}
          disabled={!onOpenSettings}
        >
          Settings
        </button>
      </div>
      <div className="flex h-[calc(100%-5.5rem)] flex-col">
        <div className="scroll-soft flex-1 overflow-y-auto px-4 pb-3">
          <ul className="space-y-4">
            {entries.map((entry) => (
              <li key={entry.id} className="lexicon-card rounded-xl p-4 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate text-sm font-semibold text-theme">{entry.keyword}</p>
                  <button
                    type="button"
                    className="text-xs font-medium text-red-400 transition hover:text-red-500"
                    onClick={() => onDelete?.(entry.id)}
                  >
                    Delete
                  </button>
                </div>
                <p className="mt-3 text-[11px] uppercase tracking-wide text-subtle">Tags</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {entry.tags.map((tag) => (
                    <span key={tag} className="tag-chip rounded-full px-3 py-0.5 text-[11px] uppercase">
                      {tag}
                    </span>
                  ))}
                </div>
              </li>
            ))}
            {!entries.length && (
              <li className="lexicon-card rounded-xl border border-dashed border-theme bg-[var(--surface-muted)] p-6 text-center text-sm text-subtle">
                No lexicon entries yet.
              </li>
            )}
          </ul>
        </div>
        <form onSubmit={handleSubmit} className="border-t border-theme px-4 py-4">
          <label className="block text-[11px] font-semibold uppercase tracking-wide text-subtle">
            Keyword
            <input
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              className="mt-1 w-full rounded border border-theme bg-[var(--surface-color)] px-3 py-2 text-sm text-theme shadow-sm focus:border-[var(--accent-color)] focus:outline-none"
              placeholder="e.g. survey"
            />
          </label>
          <label className="mt-3 block text-[11px] font-semibold uppercase tracking-wide text-subtle">
            Tags
            <input
              value={tags}
              onChange={(event) => setTags(event.target.value)}
              className="mt-1 w-full rounded border border-theme bg-[var(--surface-color)] px-3 py-2 text-sm text-theme shadow-sm focus:border-[var(--accent-color)] focus:outline-none"
              placeholder="survey, research"
            />
          </label>
          <button
            type="submit"
            className="mt-5 w-full rounded-lg bg-[var(--accent-color)] px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-[var(--accent-strong)]"
          >
            Add entry
          </button>
        </form>
      </div>
    </aside>
  );
}
