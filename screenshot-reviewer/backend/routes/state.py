"""Routes for inspecting and clearing backend selection state."""

from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException
from .. import state_manager

router = APIRouter()
logger = logging.getLogger("screenshot_reviewer")

@router.get("/", summary="Get current selection state")
def get_state() -> dict:
    """Return the current in-memory selection state."""
    return state_manager.get_current_state()

@router.post("/save", summary="Persist selection state")
async def save_state(payload: dict) -> dict:
    """Persist the provided selection state to disk."""
    try:
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Invalid state payload")
        state_manager.set_current_state(payload)
        await state_manager.save_selection_state()
        return {"status": "saved", "state": state_manager.get_current_state()}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to save selection state: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/clear", summary="Clear selection state")
async def clear_state() -> dict:
    """Clear the selection state and persist the empty payload."""
    try:
        state_manager.set_current_state({"selected": [], "timestamp": None})
        await state_manager.save_selection_state()
        logger.info("🧹 Selection state cleared via API")
        return {"status": "cleared", "state": state_manager.get_current_state()}
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to clear selection state: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))