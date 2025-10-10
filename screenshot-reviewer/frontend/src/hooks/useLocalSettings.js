import { useCallback, useEffect, useState } from "react";

import themeConfig from "../themes.json";

const STORAGE_KEY = "app-settings";
const LEGACY_KEYS = ["appSettings"];
const SETTINGS_EVENT = "app-settings:changed";

const DEFAULT_SETTINGS = {
  highlightColor: themeConfig?.light?.highlight ?? "#FFD700",
  gridColumns: 5,
  gridRows: 5,
  gridGap: 2,
};

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

const normalizeSettings = (raw = {}) => {
  const merged = { ...DEFAULT_SETTINGS, ...raw };
  merged.gridColumns = clamp(Number(merged.gridColumns) || DEFAULT_SETTINGS.gridColumns, 1, 10);
  merged.gridRows = clamp(Number(merged.gridRows) || DEFAULT_SETTINGS.gridRows, 1, 10);
  merged.gridGap = clamp(Number(merged.gridGap) || DEFAULT_SETTINGS.gridGap, 0, 32);
  return merged;
};

const loadSettings = () => {
  if (typeof window === "undefined") {
    return DEFAULT_SETTINGS;
  }
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      for (const key of LEGACY_KEYS) {
        const legacy = window.localStorage.getItem(key);
        if (legacy) {
          const normalizedLegacy = normalizeSettings(JSON.parse(legacy));
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify(normalizedLegacy));
          return normalizedLegacy;
        }
      }
      const fallback = normalizeSettings();
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(fallback));
      return fallback;
    }
    return normalizeSettings(JSON.parse(stored));
  } catch (_error) {
    return normalizeSettings();
  }
};

const applyDocumentSettings = (settings) => {
  if (typeof document === "undefined") {
    return;
  }
  document.documentElement.style.setProperty("--highlight-color", settings.highlightColor);
  document.documentElement.style.setProperty("--grid-gap", `${settings.gridGap}px`);
};

export default function useLocalSettings() {
  const [settings, setSettingsState] = useState(loadSettings);

  useEffect(() => {
    applyDocumentSettings(settings);
  }, [settings]);

  useEffect(() => {
    const handleStorage = (event) => {
      if (event.key !== STORAGE_KEY) return;
      setSettingsState(loadSettings());
    };
    const handleCustomEvent = (event) => {
      if (!event?.detail) return;
      setSettingsState(normalizeSettings(event.detail));
    };

    window.addEventListener("storage", handleStorage);
    window.addEventListener(SETTINGS_EVENT, handleCustomEvent);

    return () => {
      window.removeEventListener("storage", handleStorage);
      window.removeEventListener(SETTINGS_EVENT, handleCustomEvent);
    };
  }, []);

  const setSettings = useCallback((update) => {
    setSettingsState((previous) => {
      const base = typeof update === "function" ? update({ ...previous }) : { ...previous, ...update };
      const normalized = normalizeSettings(base);
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
      LEGACY_KEYS.forEach((key) => window.localStorage.removeItem(key));
      window.dispatchEvent(new CustomEvent(SETTINGS_EVENT, { detail: normalized }));
      return normalized;
    });
  }, []);

  return [settings, setSettings];
}
