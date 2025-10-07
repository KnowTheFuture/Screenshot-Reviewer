"""Shared selection state management utilities."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("screenshot_reviewer")

STATE_FILE = Path(__file__).resolve().parent / "selection_state.json"
current_state: Dict[str, Any] = {}


def load_selection_state() -> None:
    """Populate the in-memory state from disk if available."""
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
            current_state.clear()
            current_state.update(data)
            logger.info("🔄 Restored selection state from %s", STATE_FILE)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("⚠️ Failed to restore selection state: %s", exc)
    else:
        logger.debug("No existing selection state file found at %s", STATE_FILE)


async def save_selection_state() -> None:
    """Persist the current state to disk."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(current_state))
        logger.info("💾 Selection state saved to %s", STATE_FILE)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("❌ Failed to save selection state: %s", exc)
