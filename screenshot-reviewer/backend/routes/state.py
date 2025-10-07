"""Routes for inspecting and clearing backend selection state."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from .. import state_manager

router = APIRouter()
logger = logging.getLogger("screenshot_reviewer")


@router.get("/api/state")
def get_state() -> dict:
    """Return the current in-memory selection state."""
    return {"state": state_manager.current_state}


@router.post("/api/state/clear")
async def clear_state() -> dict:
    """Clear the selection state and persist the empty payload."""
    try:
        state_manager.current_state.clear()
        await state_manager.save_selection_state()
        logger.info("🧹 Selection state cleared via API")
        return {"status": "cleared"}
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to clear selection state: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
