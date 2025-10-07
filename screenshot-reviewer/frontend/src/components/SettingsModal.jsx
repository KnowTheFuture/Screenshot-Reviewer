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

  if (!isOpen) return null;

  const handleHighlightChange = (event) => {
    setSettings({ highlightColor: event.target.value });
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
      <div className="w-full max-w-sm rounded-lg settings-surface border border-theme p-6 shadow-lg">
        <h2 className="text-lg font-bold text-theme">Settings</h2>

        <div className="mt-4 space-y-2">
          <label htmlFor="highlight" className="block text-sm font-semibold text-theme">
            Selection Highlight
          </label>
          <input
            id="highlight"
            type="color"
            value={settings.highlightColor}
            onChange={handleHighlightChange}
            className="h-12 w-full cursor-pointer rounded border border-theme"
          />

          <label htmlFor="theme" className="block text-sm font-semibold text-theme">
            Theme
          </label>
          <select
            id="theme"
            value={theme}
            onChange={(event) => setTheme(event.target.value)}
            className="w-full rounded border border-theme p-2 text-sm capitalize"
          >
            {themeNames.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          <p className="text-xs text-theme/60">
            Background: {themeConfig[theme]?.background ?? "—"} · Text:{" "}
            {themeConfig[theme]?.text ?? "—"}
          </p>
        </div>

        {categories.length > 0 && (
          <div className="mt-6 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-theme">Category colors</h3>
              <button
                type="button"
                className="text-xs text-brand-500 hover:text-brand-600"
                onClick={resetCategoryColors}
              >
                Reset
              </button>
            </div>
            <div className="max-h-48 space-y-2 overflow-y-auto pr-1">
              {categories.map((category) => {
                const fallback =
                  categoryColors[category.name] ??
                  CATEGORY_COLORS[category.name] ??
                  CATEGORY_COLORS.default;
                return (
                  <label
                    key={category.id ?? category.name}
                    className="flex items-center justify-between gap-3 rounded border border-theme px-3 py-2 text-sm text-theme"
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
            className="flex items-center justify-center rounded bg-red-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-600"
          >
            🧹 Clear Saved Selection
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded bg-gray-200 px-4 py-2 text-sm font-medium text-gray-800 transition hover:bg-gray-300"
          >
            Close
          </button>

          <p className="mt-2 text-sm text-theme/60">
            Version: {version}
          </p>
        </div>
      </div>
    </div>
  );
}

export default SettingsModal;
