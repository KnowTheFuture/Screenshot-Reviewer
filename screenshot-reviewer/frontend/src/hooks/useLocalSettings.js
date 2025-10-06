import { useEffect, useState } from "react";

const DEFAULT_SETTINGS = {
  highlightColor: "#FFD700",
};

export default function useLocalSettings() {
  const [settings, setSettings] = useState(() => {
    try {
      const stored = localStorage.getItem("appSettings");
      return stored ? { ...DEFAULT_SETTINGS, ...JSON.parse(stored) } : DEFAULT_SETTINGS;
    } catch (_error) {
      return DEFAULT_SETTINGS;
    }
  });

  useEffect(() => {
    localStorage.setItem("appSettings", JSON.stringify(settings));
    document.documentElement.style.setProperty("--highlight-color", settings.highlightColor);
  }, [settings]);

  return [settings, setSettings];
}
