import { useCallback, useMemo, useSyncExternalStore } from "react";

import rawThemeConfig from "../themes.json";

const STORAGE_KEY = "app-theme";
const DEFAULT_THEME = "light";

const BASE_THEME = {
  background: "#ffffff",
  surface: "#ffffff",
  surfaceMuted: "#f4f4f5",
  sidebar: "#f5f5f7",
  sidebarBorder: "#e5e7eb",
  panel: "#f8fafc",
  text: "#111827",
  textMuted: "#6b7280",
  textSubtle: "#9ca3af",
  border: "#e5e7eb",
  accent: "#3b82f6",
  accentSoft: "rgba(59, 130, 246, 0.12)",
  accentStrong: "#2563eb",
  highlight: "#facc15",
  shadow: "0 12px 30px rgba(15, 23, 42, 0.1)",
  tagBg: "rgba(59, 130, 246, 0.12)",
  tagText: "#1d4ed8",
  cardTint: "rgba(59, 130, 246, 0.16)",
  fontSans: "\"Inter\", \"SF Pro Display\", -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
};

const themeVariables = Object.entries(rawThemeConfig).reduce((acc, [name, config]) => {
  const merged = { ...BASE_THEME, ...config };
  acc[name] = {
    "--bg-color": merged.background,
    "--surface-color": merged.surface,
    "--surface-muted": merged.surfaceMuted,
    "--sidebar-bg": merged.sidebar,
    "--sidebar-border": merged.sidebarBorder,
    "--panel-bg": merged.panel,
    "--text-color": merged.text,
    "--muted-text-color": merged.textMuted,
    "--subtle-text-color": merged.textSubtle,
    "--border-color": merged.border,
    "--accent-color": merged.accent,
    "--accent-soft": merged.accentSoft,
    "--accent-strong": merged.accentStrong,
    "--highlight-color": merged.highlight,
    "--card-shadow": merged.shadow,
    "--tag-bg": merged.tagBg,
    "--tag-text": merged.tagText,
    "--card-tint": merged.cardTint,
    "--font-sans": merged.fontSans,
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
  if (theme["--highlight"]) {
    document.documentElement.style.setProperty("--highlight-color", theme["--highlight"]);
  }
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
