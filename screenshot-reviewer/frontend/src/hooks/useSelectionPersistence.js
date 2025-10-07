import { useCallback, useEffect, useRef } from "react";
import { useSelectionStore } from "@/store/selectionStore.js";

const STORAGE_KEY = "screenshot-selection";

function extractSelected(payload) {
  if (payload && Array.isArray(payload.selected)) {
    return payload.selected;
  }
  if (payload && payload.state && Array.isArray(payload.state.selected)) {
    return payload.state.selected;
  }
  return [];
}

export function useSelectionPersistence(options = {}) {
  const { initialize = true } = options;

  const selected = useSelectionStore((state) => state.selected);
  const setSelection = useSelectionStore((state) => state.setSelection);
  const clear = useSelectionStore((state) => state.clear);

  const hydrationCompleteRef = useRef(false);

  useEffect(() => {
    if (!initialize || hydrationCompleteRef.current) {
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      let restored = false;
      if (typeof fetch === "function") {
        try {
          const response = await fetch("/api/state");
          if (!cancelled && response?.ok) {
            const payload = await response.json();
            const backendSelected = extractSelected(payload);
            if (backendSelected.length) {
              setSelection(backendSelected);
              console.info("✅ Restored selection from backend");
              restored = true;
            }
          }
        } catch (error) {
          if (!cancelled) {
            console.warn("⚠️ Backend unavailable, falling back to localStorage", error);
          }
        }
      }

      if (!restored && !cancelled) {
        try {
          const raw = localStorage.getItem(STORAGE_KEY);
          if (raw) {
            const storedSelection = JSON.parse(raw);
            if (Array.isArray(storedSelection) && storedSelection.length) {
              setSelection(storedSelection);
              console.info("✅ Restored selection from localStorage");
            }
          }
        } catch (error) {
          console.warn("⚠️ Failed to read selection from localStorage", error);
        }
      }

      if (!cancelled) {
        hydrationCompleteRef.current = true;
      }
    };

    hydrate();

    return () => {
      cancelled = true;
    };
  }, [initialize, setSelection]);

  useEffect(() => {
    if (!hydrationCompleteRef.current) {
      return;
    }

    const selectionArray = Array.from(selected || []);
    try {
      if (selectionArray.length) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(selectionArray));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (error) {
      console.warn("⚠️ Failed to persist selection to localStorage", error);
    }

    if (typeof fetch !== "function") {
      return;
    }

    if (selectionArray.length > 0) {
      const payload = {
        selected: selectionArray,
        timestamp: new Date().toISOString(),
      };
      fetch("/api/state/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).catch((error) => {
        console.warn("⚠️ Failed to persist selection to backend", error);
      });
    } else {
      fetch("/api/state/clear", { method: "POST" }).catch((error) => {
        console.warn("⚠️ Failed to notify backend about cleared selection", error);
      });
    }
  }, [selected]);

  const clearPersistence = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.warn("⚠️ Failed to clear persisted selection from localStorage", error);
    }
    clear();
  }, [clear]);

  return { clearPersistence };
}

export default useSelectionPersistence;