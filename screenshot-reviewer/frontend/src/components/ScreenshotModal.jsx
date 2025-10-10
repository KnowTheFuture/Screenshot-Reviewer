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
      className="w-full rounded border border-theme bg-[var(--surface-color)] px-3 py-2 text-sm text-theme shadow-sm focus:border-[var(--accent-color)] focus:outline-none"
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
      <div className="settings-surface flex max-h-full w-full max-w-5xl overflow-hidden rounded-2xl border border-theme shadow-2xl">
        <div className="hidden w-1/2 bg-black/80 md:block">
          <img
            src={draft.thumbnail || draft.path}
            alt={draft.summary || draft.path}
            className="h-full w-full object-contain"
          />
        </div>
        <form className="scroll-soft flex w-full flex-1 flex-col gap-4 overflow-y-auto bg-[var(--surface-color)] p-6" onSubmit={handleSubmit}>
          <header className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-theme">Screenshot details</h2>
            <button type="button" className="text-subtle transition hover:text-theme" onClick={onClose}>
              Close
            </button>
          </header>
          <div className="space-y-2 rounded-lg bg-[var(--surface-muted)]/60 p-4 text-sm text-muted">
            <p className="font-medium text-theme">{draft.path}</p>
            <p>Captured: {draft.created_at ? new Date(draft.created_at).toLocaleString() : "Unknown"}</p>
            <p>Group: {draft.group_id || "—"}</p>
          </div>
          <label className="text-sm font-semibold text-theme">
            Summary
            <textarea
              value={draft.summary || ""}
              onChange={(event) => handleChange("summary", event.target.value)}
              className="mt-1 w-full rounded border border-theme bg-[var(--surface-color)] px-3 py-2 text-sm text-theme shadow-sm focus:border-[var(--accent-color)] focus:outline-none"
              rows={3}
            />
          </label>
          <label className="text-sm font-semibold text-theme">
            Tags
            <TagInput value={draft.tags || []} onChange={(tags) => handleChange("tags", tags)} />
          </label>
          {suggestions?.length ? (
            <div className="space-y-2 rounded border border-[color:var(--accent-color)]/30 bg-[var(--accent-soft)] p-3 text-sm text-[var(--accent-strong)]">
              <p className="font-medium">Suggested tags</p>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    className={clsx(
                      "rounded-full border px-3 py-1 text-xs transition",
                      draft.tags?.includes(tag)
                        ? "border-[var(--accent-color)] bg-[var(--accent-color)] text-white shadow-sm"
                        : "border-[var(--accent-color)]/30 text-[var(--accent-strong)] hover:border-[var(--accent-color)]"
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
          <label className="text-sm font-semibold text-theme">
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
            <span className="text-xs text-subtle">{(draft.confidence || 0).toFixed(2)}</span>
          </label>
          <div className="flex items-center gap-4 text-sm text-theme">
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
            <button type="button" onClick={onClose} className="rounded border border-theme px-4 py-2 text-sm text-muted transition hover:border-[var(--accent-color)] hover:text-theme">
              Cancel
            </button>
            <div className="flex items-center gap-2">
              <button
                type="submit"
                className="rounded bg-[var(--accent-color)] px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-[var(--accent-strong)]"
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
