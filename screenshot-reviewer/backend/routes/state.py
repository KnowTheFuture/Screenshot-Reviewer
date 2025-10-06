"""Routes for inspecting and clearing backend selection state."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..main import current_state, save_selection_state

router = APIRouter()
logger = logging.getLogger("screenshot_reviewer")


@router.get("/api/state", tags=["State"])
def get_state() -> dict:
    """Return the current in-memory selection state."""
    return {"state": current_state}


@router.post("/api/state/clear", tags=["State"])
async def clear_state() -> dict:
    """Clear the selection state and persist the empty payload."""
    try:
        current_state.clear()
        await save_selection_state()
        logger.info("🧹 Selection state cleared via API")
        return {"status": "cleared"}
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to clear selection state: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
