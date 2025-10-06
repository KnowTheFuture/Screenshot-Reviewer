import { useEffect, useMemo, useState } from "react";
import themesConfig from "../config/theme.json";

const DEFAULT_SETTINGS = {
  theme: "light",
  highlightColor: "#FFD700",
};

function getContrastRatio(hex1, hex2) {
  const luminance = (hex) => {
    const rgb = hex
      .replace("#", "")
      .match(/.{1,2}/g)
      .map((component) => parseInt(component, 16) / 255)
      .map((value) => (value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4));
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
  };

  const l1 = luminance(hex1);
  const l2 = luminance(hex2);
  const [bright, dark] = l1 > l2 ? [l1, l2] : [l2, l1];
  return (bright + 0.05) / (dark + 0.05);
}

function ensureReadableText(background, text) {
  const ratio = getContrastRatio(background, text);
  if (ratio >= 4.5) {
    return text;
  }
  return getContrastRatio(background, "#FFFFFF") >= 4.5 ? "#FFFFFF" : "#111111";
}

export function useLocalSettings() {
  const [settings, setSettings] = useState(() => {
    const stored = localStorage.getItem("appSettings");
    if (stored) {
      try {
        return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
      } catch (_err) {
        return DEFAULT_SETTINGS;
      }
    }
    return DEFAULT_SETTINGS;
  });

  const themes = useMemo(() => themesConfig, []);

  useEffect(() => {
    localStorage.setItem("appSettings", JSON.stringify(settings));
  }, [settings]);

  useEffect(() => {
    const theme = themes[settings.theme] || themes.light;
    if (!theme) return;

    const textColor = ensureReadableText(theme.background, theme.text);

    document.documentElement.style.setProperty("--background-color", theme.background);
    document.documentElement.style.setProperty("--surface-color", theme.surface);
    document.documentElement.style.setProperty("--text-color", textColor);
    document.documentElement.style.setProperty("--border-color", theme.border);

    const highlight = settings.highlightColor || theme.highlight || DEFAULT_SETTINGS.highlightColor;
    document.documentElement.style.setProperty("--highlight-color", highlight);

    document.body.dataset.theme = settings.theme;
  }, [settings, themes]);

  const updateSettings = (partial) => {
    setSettings((prev) => ({ ...prev, ...partial }));
  };

  return { settings, updateSettings, themes };
}

export default useLocalSettings;
