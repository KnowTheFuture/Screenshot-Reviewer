import { useCallback, useMemo, useSyncExternalStore } from "react";

import rawThemeConfig from "../themes.json";

const STORAGE_KEY = "app-theme";
const DEFAULT_THEME = "light";

const themeVariables = Object.entries(rawThemeConfig).reduce((acc, [name, config]) => {
  const background = config.background ?? "#ffffff";
  const text = config.text ?? "#111111";
  const border = config.border ?? "#d1d5db";
  const surface = config.surface ?? background;

  acc[name] = {
    "--bg-color": background,
    "--text-color": text,
    "--surface-color": surface,
    "--border-color": border,
  };
  return acc;
}, {});

let currentTheme = DEFAULT_THEME;
const subscribers = new Set();

const notifySubscribers = () => {
  subscribers.forEach((callback) => callback());
};

const applyThemeVariables = (themeName) => {
  if (typeof document === "undefined") {
    return;
  }
  const theme = themeVariables[themeName] ?? themeVariables[DEFAULT_THEME];
  Object.entries(theme).forEach(([cssVar, value]) => {
    document.documentElement.style.setProperty(cssVar, value);
  });
  document.body.dataset.theme = themeName;
};

const loadInitialTheme = () => {
  if (typeof window === "undefined") {
    return DEFAULT_THEME;
  }
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored && themeVariables[stored]) {
    return stored;
  }
  return DEFAULT_THEME;
};

if (typeof window !== "undefined") {
  currentTheme = loadInitialTheme();
  applyThemeVariables(currentTheme);
}

if (typeof window !== "undefined") {
  window.addEventListener("storage", (event) => {
    if (event.key !== STORAGE_KEY) return;
    const nextName = event.newValue && themeVariables[event.newValue] ? event.newValue : DEFAULT_THEME;
    if (nextName === currentTheme) return;
    currentTheme = nextName;
    applyThemeVariables(currentTheme);
    notifySubscribers();
  });
}

const setTheme = (themeName) => {
  const next = themeVariables[themeName] ? themeName : DEFAULT_THEME;
  currentTheme = next;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, next);
  }
  applyThemeVariables(next);
  notifySubscribers();
};

const subscribe = (callback) => {
  subscribers.add(callback);
  return () => {
    subscribers.delete(callback);
  };
};

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, () => currentTheme, () => currentTheme);

  const themeNames = useMemo(() => Object.keys(themeVariables), []);

  const setAndApplyTheme = useCallback((themeName) => {
    setTheme(themeName);
  }, []);

  const definitions = useMemo(() => rawThemeConfig, []);

  return {
    theme,
    themes: themeVariables,
    themeNames,
    themeConfig: definitions,
    setTheme: setAndApplyTheme,
  };
}

export default useTheme;
