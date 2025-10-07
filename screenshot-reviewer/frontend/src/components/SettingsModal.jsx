import axios from "axios";
import { useSelectionStore } from "../store/selectionStore.js";
import useLocalSettings from "../hooks/useLocalSettings.js";
import pkg from "../../package.json";

const STORAGE_KEY = "selection";

function SettingsModal({
  isOpen,
  onClose,
  onClearSelection,
  settings: controlledSettings,
  onChangeSettings,
  themes,
}) {
  const [localSettings, setLocalSettings] = useLocalSettings();
  const clearSelection = useSelectionStore((state) => state.clear);

  void themes;

  const settings = controlledSettings ?? localSettings;
  const setSettings =
    onChangeSettings ?? ((update) => setLocalSettings({ ...settings, ...update }));
  const version = (pkg && pkg.version) ? pkg.version : "dev";

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
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem("screenshot-selection");
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
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-lg dark:bg-gray-800">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white">Settings</h2>

        <div className="mt-4 space-y-2">
          <label
            htmlFor="highlight"
            className="block text-sm font-semibold text-gray-700 dark:text-gray-200"
          >
            Selection Highlight
          </label>
          <input
            id="highlight"
            type="color"
            value={settings.highlightColor}
            onChange={handleColorChange}
            className="h-12 w-full cursor-pointer rounded border border-gray-300"
          />
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