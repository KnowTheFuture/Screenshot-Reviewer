import { useHotkeys } from "react-hotkeys-hook";
import useSelectionStore from "../store/selectionStore.js";

export default function useKeyboardShortcuts() {
  useHotkeys(
    "left",
    () => useSelectionStore.getState().goToPrev(),
    { enableOnFormTags: false }
  );
  useHotkeys(
    "right",
    () => useSelectionStore.getState().goToNext(),
    { enableOnFormTags: false }
  );
  useHotkeys(
    "enter",
    () => useSelectionStore.getState().goToNext(),
    { enableOnFormTags: false }
  );
  useHotkeys(
    "ctrl+s,cmd+s",
    (event) => {
      event.preventDefault();
      useSelectionStore.getState().triggerSave();
    },
    { enableOnFormTags: true }
  );
}
