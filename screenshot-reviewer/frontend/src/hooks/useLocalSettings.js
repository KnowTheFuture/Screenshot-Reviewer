import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "appSettings";
const SETTINGS_EVENT = "app-settings:changed";

const DEFAULT_SETTINGS = {
  highlightColor: "#FFD700",
};

const loadSettings = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_SETTINGS));
      return DEFAULT_SETTINGS;
    }
    const parsed = JSON.parse(stored);
    return { ...DEFAULT_SETTINGS, ...parsed };
  } catch (_error) {
    return DEFAULT_SETTINGS;
  }
};

const applyHighlight = (settings) => {
  document.documentElement.style.setProperty("--highlight-color", settings.highlightColor);
};

export default function useLocalSettings() {
  const [settings, setSettingsState] = useState(loadSettings);

  useEffect(() => {
    applyHighlight(settings);
  }, [settings]);

  useEffect(() => {
    const handleStorage = (event) => {
      if (event.key !== STORAGE_KEY) return;
      setSettingsState(loadSettings());
    };
    const handleCustomEvent = (event) => {
      if (!event?.detail) return;
      setSettingsState({ ...DEFAULT_SETTINGS, ...event.detail });
    };

    window.addEventListener("storage", handleStorage);
    window.addEventListener(SETTINGS_EVENT, handleCustomEvent);

    return () => {
      window.removeEventListener("storage", handleStorage);
      window.removeEventListener(SETTINGS_EVENT, handleCustomEvent);
    };
  }, []);

  const setSettings = useCallback((update) => {
    setSettingsState((prev) => {
      const next =
        typeof update === "function" ? update({ ...prev }) : { ...prev, ...update };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      window.dispatchEvent(new CustomEvent(SETTINGS_EVENT, { detail: next }));
      return next;
    });
  }, []);

  return [settings, setSettings];
}
