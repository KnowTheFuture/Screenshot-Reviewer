import axios from "axios";

import useLocalSettings from "../hooks/useLocalSettings.js";
import { useSelectionStore } from "../store/selectionStore.js";
import themes from "../themes.json";
import pkg from "../../package.json";

const LEGACY_KEYS = ["selection", "screenshot-selection"];

function SettingsModal({
  isOpen,
  onClose,
  onClearSelection,
  settings: controlledSettings,
  onChangeSettings,
}) {
  const [localSettings, setLocalSettings] = useLocalSettings();
  const clearSelection = useSelectionStore((state) => state.clear);

  const settings = controlledSettings ?? localSettings;
  const setSettings = onChangeSettings ?? ((update) => setLocalSettings(update));
  const version = pkg?.version ?? "dev";

  if (!isOpen) return null;

  const handleColorChange = (event) => {
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
          <label
            htmlFor="highlight"
            className="block text-sm font-semibold text-theme"
          >
            Selection Highlight
          </label>
          <input
            id="highlight"
            type="color"
            value={settings.highlightColor}
            onChange={handleColorChange}
            className="h-12 w-full cursor-pointer rounded border border-theme"
          />

          <label
            htmlFor="theme"
            className="block text-sm font-semibold text-theme"
          >
            Theme
          </label>
          <select
            id="theme"
            value={settings.themeName}
            onChange={(event) => setSettings({ themeName: event.target.value })}
            className="w-full rounded border border-theme p-2 text-sm capitalize"
          >
            {Object.keys(themes).map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>

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

          <p className="text-sm text-gray-500 mt-2">
            Version: {version}
          </p>
        </div>
      </div>
    </div>
  );
}

export default SettingsModal;
