import { useEffect } from "react";

export function useSelectionPersistence(selected, setSelection) {
  // Restore on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem("selection");
      if (stored) {
        const ids = JSON.parse(stored);
        if (Array.isArray(ids) && setSelection) {
          setSelection(ids);
        }
      }
    } catch (err) {
      console.warn("⚠️ Failed to restore selection from storage", err);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const saveState = () => {
      try {
        localStorage.setItem("selection", JSON.stringify(Array.from(selected || [])));
      } catch (err) {
        console.warn("⚠️ Failed to persist selection", err);
      }
    };

    window.addEventListener("beforeunload", saveState);
    return () => {
      saveState();
      window.removeEventListener("beforeunload", saveState);
    };
  }, [selected]);
}

export default useSelectionPersistence;
