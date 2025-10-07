"""Centralized selection state management for the backend."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("screenshot_reviewer")

STATE_FILE = Path(__file__).resolve().parent / "state.json"


def _default_state() -> Dict[str, Any]:
    return {"selected": [], "timestamp": None}


def _normalize_state(raw: Dict[str, Any]) -> Dict[str, Any]:
    selected = raw.get("selected", [])
    if isinstance(selected, set):
        selected = list(selected)
    elif not isinstance(selected, list):
        try:
            selected = list(selected)
        except TypeError:
            selected = []
    # Drop duplicates while preserving order
    deduped_selected = list(dict.fromkeys(selected))
    timestamp = raw.get("timestamp")
    return {"selected": deduped_selected, "timestamp": timestamp}


current_state: Dict[str, Any] = _default_state()


def load_selection_state() -> Dict[str, Any]:
    """Populate the in-memory state from disk if available, returning the state."""
    global current_state

    if STATE_FILE.exists():
        try:
            payload = json.loads(STATE_FILE.read_text())
            if not isinstance(payload, dict):
                raise ValueError("state file must contain a JSON object")
            current_state = _normalize_state(payload)
            logger.info("✅ Loaded state (%d items)", len(current_state.get("selected", [])))
        except Exception as exc:  # pragma: no cover - defensive
            current_state = _default_state()
            logger.warning("⚠️ Failed to load state.json: %s", exc)
    else:
        current_state = _default_state()
        logger.info("ℹ️ No existing state.json, using defaults")

    return current_state


async def save_selection_state() -> None:
    """Persist the current state to disk asynchronously."""
    snapshot = _normalize_state(current_state)
    try:
        await asyncio.to_thread(_write_state_file, snapshot)
        logger.info("💾 Saved state (%d items)", len(snapshot.get("selected", [])))
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("❌ Save failed: %s", exc)


def _write_state_file(state: Dict[str, Any] | None = None) -> None:
    """Write the provided state (or current state) to disk atomically."""
    payload = _normalize_state(state or current_state)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = STATE_FILE.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    tmp_path.replace(STATE_FILE)


def get_current_state() -> Dict[str, Any]:
    """Return the in-memory state reference."""
    return current_state


def set_current_state(new_state: Dict[str, Any]) -> None:
    """Replace the in-memory state, primarily used for tests."""
    global current_state
    current_state = _normalize_state(new_state)
