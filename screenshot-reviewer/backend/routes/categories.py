"""Routes for managing screenshot categories."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from ..models import Category, CategoryCreate, CategoryUpdate, ScreenshotStatus
from ..storage import get_item_or_404, load_categories, load_screenshots, save_categories

router = APIRouter()
logger = logging.getLogger(__name__)

FALLBACK_CATEGORIES = [
    {"id": "default-1", "name": "General"},
    {"id": "default-2", "name": "Important"},
    {"id": "default-3", "name": "To Review"},
]

def _annotate_counts(categories: List[dict]) -> List[Category]:
    screenshots = load_screenshots()
    for category in categories:
        category_id = category.get("id")
        count = 0
        pending = 0
        for item in screenshots:
            if item.get("primary_category") == category_id:
                count += 1
                status = str(item.get("status", ScreenshotStatus.PENDING.value))
                if status in {ScreenshotStatus.PENDING.value, ScreenshotStatus.DEFERRED.value}:
                    pending += 1
        category["count"] = count
        category["pending"] = pending
    return [Category.model_validate(cat) for cat in categories]


@router.get("", response_model=List[Category])
def list_categories():
    try:
        categories = load_categories()
        if not isinstance(categories, list):
            logger.warning("Unexpected categories payload %s; returning fallback catalogue", type(categories))
            return _annotate_counts([dict(cat) for cat in FALLBACK_CATEGORIES])
        if not categories:
            logger.info("No categories found on disk, using fallback defaults")
            return _annotate_counts([dict(cat) for cat in FALLBACK_CATEGORIES])
        return _annotate_counts(categories)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in list_categories")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("", response_model=Category, status_code=201)
def create_category(payload: CategoryCreate):
    try:
        categories = load_categories()
        if any(cat.get("name", "").lower() == payload.name.lower() for cat in categories):
            raise HTTPException(status_code=409, detail="Category name already exists")
        category = {
            "id": uuid4().hex,
            "name": payload.name,
            "description": payload.description,
            "created_at": datetime.utcnow().isoformat(),
        }
        categories.append(category)
        save_categories(categories)
        return _annotate_counts([category])[0]
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in create_category")
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/{category_id}", response_model=Category)
def update_category(category_id: str, payload: CategoryUpdate):
    try:
        categories = load_categories()
        category = get_item_or_404(categories, category_id, entity="Category")
        update_data = payload.model_dump(exclude_unset=True)
        if "name" in update_data:
            candidate = update_data["name"].lower()
            if any(cat.get("id") != category_id and cat.get("name", "").lower() == candidate for cat in categories):
                raise HTTPException(status_code=409, detail="Category name already exists")
        category.update(update_data)
        category["updated_at"] = datetime.utcnow().isoformat()
        save_categories(categories)
        return _annotate_counts([category])[0]
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in update_category")
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{category_id}", response_model=dict)
def delete_category(category_id: str):
    try:
        categories = load_categories()
        category = get_item_or_404(categories, category_id, entity="Category")
        categories = [cat for cat in categories if cat.get("id") != category_id]
        save_categories(categories)
        return {"deleted": category_id}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in delete_category")
        raise HTTPException(status_code=500, detail=str(exc))
