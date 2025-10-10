import axios from "axios";

import useLocalSettings from "../hooks/useLocalSettings.js";
import useTheme from "../hooks/useTheme.js";
import useCategoryColorStore from "../store/categoryColorStore.js";
import { CATEGORY_COLORS } from "../constants/categoryColors.js";
import useSelectionStore from "../store/selectionStore.js";
import pkg from "../../package.json";

const LEGACY_KEYS = ["selection", "screenshot-selection"];

function SettingsModal({
  isOpen,
  onClose,
  onClearSelection,
  settings: controlledSettings,
  onChangeSettings,
  categories = [],
}) {
  const [localSettings, setLocalSettings] = useLocalSettings();
  const clearSelection = useSelectionStore((state) => state.clear);
  const { theme, themeNames, setTheme, themeConfig } = useTheme();
  const categoryColors = useCategoryColorStore((state) => state.colors);
  const setCategoryColor = useCategoryColorStore((state) => state.setColor);
  const resetCategoryColors = useCategoryColorStore((state) => state.resetColors);

  const settings = controlledSettings ?? localSettings;
  const setSettings = onChangeSettings ?? ((update) => setLocalSettings(update));
  const version = pkg?.version ?? "dev";
  const totalImages = (settings?.gridColumns ?? 1) * (settings?.gridRows ?? 1);

  if (!isOpen) return null;

  const handleHighlightChange = (event) => {
    setSettings({ highlightColor: event.target.value });
  };

  const handleGridColumnsChange = (event) => {
    setSettings({ gridColumns: Number(event.target.value) });
  };

  const handleGridRowsChange = (event) => {
    setSettings({ gridRows: Number(event.target.value) });
  };

  const handleGridGapChange = (event) => {
    setSettings({ gridGap: Number(event.target.value) });
  };

  const handleClearSelection = async () => {
    if (onClearSelection) {
      await onClearSelection();
      return;
    }

    try {
      LEGACY_KEYS.forEach((key) => localStorage.removeItem(key));
    } catch (error) {
      console.warn("⚠️ Failed to clear selection from localStorage", error);
    }

    clearSelection?.();

    try {
      await axios.post("/api/state/clear");
    } catch (error) {
      console.warn("⚠️ Failed to notify backend about cleared selection", error);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-sm rounded-2xl settings-surface border border-theme p-6 shadow-2xl">
        <h2 className="text-lg font-bold text-theme tracking-tight">Settings</h2>

        <div className="mt-4 space-y-3">
          <label htmlFor="highlight" className="block text-sm font-semibold uppercase tracking-wide text-subtle">
            Selection Highlight
          </label>
          <input
            id="highlight"
            type="color"
            value={settings.highlightColor}
            onChange={handleHighlightChange}
            className="h-12 w-full cursor-pointer rounded border border-theme bg-[var(--surface-color)] shadow-inner"
          />

          <label htmlFor="theme" className="block text-sm font-semibold uppercase tracking-wide text-subtle">
            Theme
          </label>
          <select
            id="theme"
            value={theme}
            onChange={(event) => setTheme(event.target.value)}
            className="w-full rounded border border-theme bg-[var(--surface-color)] p-2 text-sm capitalize text-theme shadow-sm focus:border-[var(--accent-color)] focus:outline-none"
          >
            {themeNames.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          <p className="text-xs text-subtle">
            Background: {themeConfig[theme]?.background ?? "—"} · Text:{" "}
            {themeConfig[theme]?.text ?? "—"}
          </p>
        </div>

        <div className="mt-6 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-subtle">Grid layout</h3>
            <span className="text-xs text-muted">
              {settings.gridColumns} × {settings.gridRows} ({totalImages} images)
            </span>
          </div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-subtle">
            Columns
            <div className="mt-2 flex items-center gap-3">
              <input
                type="range"
                min="1"
                max="10"
                value={settings.gridColumns ?? 1}
                onChange={handleGridColumnsChange}
                className="flex-1"
              />
              <span className="w-6 text-right text-sm text-theme">{settings.gridColumns}</span>
            </div>
          </label>
          <label className="block text-xs font-semibold uppercase tracking-wide text-subtle">
            Rows
            <div className="mt-2 flex items-center gap-3">
              <input
                type="range"
                min="1"
                max="10"
                value={settings.gridRows ?? 1}
                onChange={handleGridRowsChange}
                className="flex-1"
              />
              <span className="w-6 text-right text-sm text-theme">{settings.gridRows}</span>
            </div>
          </label>
          <label className="block text-xs font-semibold uppercase tracking-wide text-subtle">
            Image gap (px)
            <div className="mt-2 flex items-center gap-3">
              <input
                type="range"
                min="0"
                max="32"
                step="1"
                value={settings.gridGap ?? 0}
                onChange={handleGridGapChange}
                className="flex-1"
              />
              <span className="w-8 text-right text-sm text-theme">{settings.gridGap}</span>
            </div>
          </label>
        </div>

        {categories.length > 0 && (
          <div className="mt-6 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-subtle">Category colors</h3>
              <button
                type="button"
                className="text-xs font-semibold text-[var(--accent-color)] transition hover:text-[var(--accent-strong)]"
                onClick={resetCategoryColors}
              >
                Reset
              </button>
            </div>
            <div className="scroll-soft max-h-48 space-y-2 overflow-y-auto pr-1">
              {categories.map((category) => {
                const fallback =
                  categoryColors[category.name] ??
                  CATEGORY_COLORS[category.name] ??
                  CATEGORY_COLORS.default;
                return (
                  <label
                    key={category.id ?? category.name}
                    className="flex items-center justify-between gap-3 rounded-lg border border-theme bg-[var(--surface-color)] px-3 py-2 text-sm text-theme shadow-sm"
                  >
                    <span className="truncate">{category.name}</span>
                    <input
                      type="color"
                      value={fallback}
                      onChange={(event) => setCategoryColor(category.name, event.target.value)}
                      className="h-8 w-12 cursor-pointer rounded border border-theme bg-transparent p-0"
                    />
                  </label>
                );
              })}
            </div>
          </div>
        )}

        <div className="mt-6 flex flex-col gap-3">
          <button
            type="button"
            onClick={handleClearSelection}
            className="flex items-center justify-center rounded-lg bg-red-500 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-red-600"
          >
            🧹 Clear Saved Selection
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-theme bg-[var(--surface-muted)] px-4 py-2 text-sm font-semibold text-theme transition hover:border-[var(--accent-color)] hover:text-[var(--accent-color)]"
          >
            Close
          </button>

          <p className="mt-2 text-sm text-subtle">
            Version: {version}
          </p>
        </div>
      </div>
    </div>
  );
}

export default SettingsModal;
