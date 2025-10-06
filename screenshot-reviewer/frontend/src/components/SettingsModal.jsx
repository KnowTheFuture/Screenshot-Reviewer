import useLocalSettings from "../hooks/useLocalSettings.js";

export default function SettingsModal({ isOpen, onClose }) {
  const [settings, setSettings] = useLocalSettings();

  if (!isOpen) return null;

  const handleColorChange = (event) => {
    setSettings({ ...settings, highlightColor: event.target.value });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-lg dark:bg-gray-800">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white">Settings</h2>
        <div className="mt-4 space-y-2">
          <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200">Highlight Color</label>
          <input
            type="color"
            value={settings.highlightColor}
            onChange={handleColorChange}
            className="h-12 w-full cursor-pointer rounded border border-gray-300"
          />
        </div>
        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded bg-gray-200 px-4 py-2 text-sm font-medium text-gray-800 hover:bg-gray-300"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
