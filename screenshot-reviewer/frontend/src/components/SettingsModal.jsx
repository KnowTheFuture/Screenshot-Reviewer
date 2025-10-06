import { useState } from "react";
import axios from "axios";

const DEFAULT_HIGHLIGHT = "#FFD700";

export default function SettingsModal({
  isOpen,
  onClose,
  settings,
  themes,
  onChangeSettings,
  onCleared,
}) {
  const [status, setStatus] = useState("");

  if (!isOpen) return null;

  const handleHighlightChange = (event) => {
    onChangeSettings?.({ highlightColor: event.target.value });
  };

  const handleThemeChange = (event) => {
    onChangeSettings?.({ theme: event.target.value });
  };

  const handleClearSelection = async () => {
    try {
      localStorage.removeItem("selection");
      await axios.post("/api/state/clear");
      setStatus("✅ Selection cleared");
      onCleared?.();
    } catch (error) {
      console.error(error);
      setStatus("❌ Failed to clear selection");
    }
  };

  const handleRestoreDefaults = () => {
    onChangeSettings?.({ theme: "light", highlightColor: DEFAULT_HIGHLIGHT });
    setStatus("Settings restored to defaults");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="settings-surface w-full max-w-md rounded-xl border border-theme p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-theme">Settings</h2>
          <button type="button" className="text-theme/70" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="mt-4 space-y-4 text-sm text-theme">
          <div>
            <label className="block font-medium" htmlFor="theme-select">
              Interface theme
            </label>
            <select
              id="theme-select"
              value={settings.theme}
              onChange={handleThemeChange}
              className="mt-1 w-full rounded border border-theme px-3 py-2"
            >
              {Object.entries(themes).map(([key, value]) => (
                <option key={key} value={key}>
                  {value.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-2 block font-medium" htmlFor="highlight-color">
              Selection highlight
            </label>
            <input
              id="highlight-color"
              type="color"
              value={settings.highlightColor}
              onChange={handleHighlightChange}
              className="h-10 w-16 cursor-pointer rounded border border-theme"
            />
          </div>
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={handleClearSelection}
              className="rounded bg-red-500 px-4 py-2 text-sm font-medium text-white hover:bg-red-600"
            >
              🧹 Clear saved selection
            </button>
            <button
              type="button"
              onClick={handleRestoreDefaults}
              className="rounded border border-theme px-4 py-2 text-sm text-theme hover:bg-black/5"
            >
              Reset to defaults
            </button>
          </div>
          {status && <p className="text-xs text-theme/70">{status}</p>}
        </div>
      </div>
    </div>
  );
}
