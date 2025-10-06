"""Routes for managing screenshot categories."""

from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from ..models import Category, CategoryCreate, CategoryUpdate, ScreenshotStatus
from ..storage import get_item_or_404, load_categories, load_screenshots, save_categories

router = APIRouter()


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


@router.get("/", response_model=List[Category])
def list_categories():
    categories = load_categories()
    return _annotate_counts(categories)


@router.post("/", response_model=Category, status_code=201)
def create_category(payload: CategoryCreate):
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


@router.put("/{category_id}", response_model=Category)
def update_category(category_id: str, payload: CategoryUpdate):
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


@router.delete("/{category_id}", response_model=dict)
def delete_category(category_id: str):
    categories = load_categories()
    category = get_item_or_404(categories, category_id, entity="Category")
    categories = [cat for cat in categories if cat.get("id") != category_id]
    save_categories(categories)
    return {"deleted": category_id}
