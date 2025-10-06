import { useState } from "react";

export default function LexiconPanel({ entries, onCreate, onDelete }) {
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
    <aside className="w-80 border-l border-slate-200 bg-white">
      <div className="px-5 py-4">
        <h2 className="text-lg font-semibold text-slate-900">Lexicon</h2>
        <p className="text-xs text-slate-500">Keywords that auto-suggest tags.</p>
      </div>
      <div className="flex h-[calc(100%-5rem)] flex-col">
        <div className="flex-1 overflow-y-auto px-5">
          <ul className="space-y-3">
            {entries.map((entry) => (
              <li key={entry.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-slate-700">{entry.keyword}</p>
                  <button
                    type="button"
                    className="text-xs text-red-500 hover:text-red-600"
                    onClick={() => onDelete?.(entry.id)}
                  >
                    Delete
                  </button>
                </div>
                <p className="mt-2 text-xs uppercase tracking-wide text-slate-400">Tags</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {entry.tags.map((tag) => (
                    <span key={tag} className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                      {tag}
                    </span>
                  ))}
                </div>
              </li>
            ))}
            {!entries.length && (
              <li className="rounded-lg border border-dashed border-slate-200 p-6 text-center text-slate-400">
                No lexicon entries yet.
              </li>
            )}
          </ul>
        </div>
        <form onSubmit={handleSubmit} className="border-t border-slate-200 px-5 py-4">
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">
            Keyword
            <input
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              placeholder="e.g. survey"
            />
          </label>
          <label className="mt-3 block text-xs font-medium uppercase tracking-wide text-slate-500">
            Tags
            <input
              value={tags}
              onChange={(event) => setTags(event.target.value)}
              className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              placeholder="survey, research"
            />
          </label>
          <button
            type="submit"
            className="mt-4 w-full rounded bg-brand-500 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-600"
          >
            Add entry
          </button>
        </form>
      </div>
    </aside>
  );
}
