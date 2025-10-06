import { useEffect, useState } from "react";
import clsx from "clsx";

function TagInput({ value, onChange }) {
  const [input, setInput] = useState(value.join(", "));

  useEffect(() => {
    setInput(value.join(", "));
  }, [value]);

  const handleBlur = () => {
    const tags = input
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
    onChange(tags);
  };

  return (
    <input
      className="w-full rounded border border-slate-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
      value={input}
      onChange={(event) => setInput(event.target.value)}
      onBlur={handleBlur}
      placeholder="Tag1, Tag2, ..."
    />
  );
}

export default function ScreenshotModal({
  isOpen,
  screenshot,
  onClose,
  onSave,
  suggestions,
}) {
  const [draft, setDraft] = useState(null);

  useEffect(() => {
    if (screenshot) {
      setDraft({ ...screenshot });
    }
  }, [screenshot]);

  if (!isOpen || !screenshot) return null;

  const handleChange = (key, value) => {
    setDraft((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSave?.(draft);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-6">
      <div className="flex max-h-full w-full max-w-5xl overflow-hidden rounded-2xl bg-white shadow-xl">
        <div className="hidden w-1/2 bg-slate-900 md:block">
          <img
            src={draft.thumbnail || draft.path}
            alt={draft.summary || draft.path}
            className="h-full w-full object-contain"
          />
        </div>
        <form className="flex w-full flex-1 flex-col gap-4 overflow-y-auto p-6" onSubmit={handleSubmit}>
          <header className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Screenshot details</h2>
            <button type="button" className="text-slate-400 hover:text-slate-600" onClick={onClose}>
              Close
            </button>
          </header>
          <div className="space-y-2 text-sm text-slate-500">
            <p className="font-medium text-slate-700">{draft.path}</p>
            <p>Captured: {draft.created_at ? new Date(draft.created_at).toLocaleString() : "Unknown"}</p>
            <p>Group: {draft.group_id || "—"}</p>
          </div>
          <label className="text-sm font-medium text-slate-600">
            Summary
            <textarea
              value={draft.summary || ""}
              onChange={(event) => handleChange("summary", event.target.value)}
              className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              rows={3}
            />
          </label>
          <label className="text-sm font-medium text-slate-600">
            Tags
            <TagInput value={draft.tags || []} onChange={(tags) => handleChange("tags", tags)} />
          </label>
          {suggestions?.length ? (
            <div className="space-y-2 rounded border border-brand-100 bg-brand-50 p-3 text-sm text-brand-700">
              <p className="font-medium">Suggested tags</p>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    className={clsx(
                      "rounded-full border px-3 py-1 text-xs",
                      draft.tags?.includes(tag)
                        ? "border-brand-500 bg-brand-500 text-white"
                        : "border-brand-200 text-brand-600"
                    )}
                    onClick={() => {
                      const tags = new Set(draft.tags || []);
                      if (tags.has(tag)) tags.delete(tag);
                      else tags.add(tag);
                      handleChange("tags", Array.from(tags));
                    }}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
          <label className="text-sm font-medium text-slate-600">
            Confidence
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={draft.confidence || 0}
              onChange={(event) => handleChange("confidence", Number(event.target.value))}
              className="mt-2 w-full"
            />
            <span className="text-xs text-slate-500">{(draft.confidence || 0).toFixed(2)}</span>
          </label>
          <div className="flex items-center gap-4 text-sm">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={draft.status === "re-review"}
                onChange={(event) => handleChange("status", event.target.checked ? "re-review" : "reviewed")}
              />
              Mark for re-review
            </label>
            <label className="flex items-center gap-2 text-red-500">
              <input
                type="checkbox"
                checked={draft.status === "deleted"}
                onChange={(event) => handleChange("status", event.target.checked ? "deleted" : "reviewed")}
              />
              Mark for deletion
            </label>
          </div>
          <div className="mt-auto flex justify-between pt-4">
            <button type="button" onClick={onClose} className="rounded border border-slate-300 px-4 py-2 text-sm">
              Cancel
            </button>
            <div className="flex items-center gap-2">
              <button
                type="submit"
                className="rounded bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600"
              >
                Save changes (Enter)
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
