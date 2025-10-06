"""Routes for screenshot CRUD and batch operations."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query

from ..models import (
    BatchUpdateRequest,
    GroupsPayload,
    GroupSummary,
    PaginatedResponse,
    Screenshot,
    ScreenshotFilter,
    ScreenshotStatus,
    ScreenshotUpdate,
)
from ..storage import load_lexicon, load_screenshots, save_screenshots

router = APIRouter()
logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.6
GROUP_WINDOW_MINUTES = 3
FILES_BASE_URL = os.getenv("BACKEND_PUBLIC_URL", "http://127.0.0.1:8000")


def _enrich_screenshot(item: dict, base_url: str = FILES_BASE_URL) -> dict:
    path = item.get("path")
    enriched = item.copy()

    if path and os.path.exists(path):
        filename = os.path.basename(path)
        base = base_url.rstrip("/")
        enriched["url"] = f"{base}/files/{quote(filename)}"
    else:
        logger.warning("Missing file for screenshot %s: %s", item.get("id"), path)
        enriched["url"] = None

    return enriched


def _match_filter(item: dict, *, filter_mode: ScreenshotFilter) -> bool:
    status = str(item.get("status", ScreenshotStatus.PENDING.value))
    confidence = float(item.get("confidence", 0) or 0)
    if filter_mode == ScreenshotFilter.ALL:
        return True
    if filter_mode == ScreenshotFilter.PENDING:
        no_category = not (item.get("primary_category") or "").strip()
        return status in {ScreenshotStatus.PENDING.value, ScreenshotStatus.DEFERRED.value} or no_category
    if filter_mode == ScreenshotFilter.DEFERRED:
        return status == ScreenshotStatus.DEFERRED.value
    if filter_mode == ScreenshotFilter.RE_REVIEW:
        return status == ScreenshotStatus.RE_REVIEW.value
    if filter_mode == ScreenshotFilter.LOW_CONFIDENCE:
        return confidence < LOW_CONFIDENCE_THRESHOLD
    return True


def _apply_search(item: dict, search: str) -> bool:
    haystack = " ".join(
        [
            item.get("path", ""),
            item.get("summary", ""),
            " ".join(item.get("tags", [])),
            item.get("ocr_text", ""),
        ]
    ).lower()
    return search.lower() in haystack


def _generate_suggestions(item: dict) -> List[str]:
    lexicon = load_lexicon()
    text = f"{item.get('path', '')} {item.get('ocr_text', '')}".lower()
    suggestions: List[str] = []
    for entry in lexicon:
        keyword = entry.get("keyword", "").lower()
        if keyword and keyword in text:
            suggestions.extend(entry.get("tags", []))
    return sorted({tag for tag in suggestions if tag})


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _bucket_id(created_at: Optional[datetime]) -> str:
    if created_at is None:
        return "grp-unknown"
    window_seconds = GROUP_WINDOW_MINUTES * 60
    bucket = int(created_at.timestamp()) // window_seconds
    return f"grp-{bucket}"


def _infer_groups(items: List[dict]) -> GroupsPayload:
    if not items:
        return GroupsPayload(items=[], current_index=0)

    groups: dict[str, List[dict]] = {}
    for entry in items:
        created_at = _parse_datetime(entry.get("created_at"))
        group_key = _bucket_id(created_at)
        groups.setdefault(group_key, []).append(entry)
        entry["group_id"] = group_key

    summaries: List[GroupSummary] = []
    for group_id, group_items in groups.items():
        group_items.sort(
            key=lambda entry: _parse_datetime(entry.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)
        )
        summaries.append(
            GroupSummary(
                group_id=group_id,
                size=len(group_items),
                start=_parse_datetime(group_items[0].get("created_at")),
                end=_parse_datetime(group_items[-1].get("created_at")),
            )
        )

    summaries.sort(key=lambda summary: summary.start or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return GroupsPayload(items=summaries, current_index=0)


def _with_groups(items: List[dict], group_id: Optional[str]) -> tuple[List[dict], GroupsPayload]:
    payload = _infer_groups(items)
    if group_id:
        for index, group in enumerate(payload.items):
            if group.group_id == group_id:
                payload.current_index = index
                filtered = [entry for entry in items if entry.get("group_id") == group_id]
                return filtered, payload
        return [], payload
    return items, payload


def _paginate(items: List[dict], page: int, page_size: int) -> List[dict]:
    start = max(page - 1, 0) * page_size
    end = start + page_size
    return items[start:end]


def _build_progress(dataset: List[dict]) -> dict:
    total = len(dataset)
    reviewed = sum(
        1 for item in dataset if str(item.get("status")) == ScreenshotStatus.REVIEWED.value
    )
    deferred = sum(
        1 for item in dataset if str(item.get("status")) == ScreenshotStatus.DEFERRED.value
    )
    re_review = sum(
        1 for item in dataset if str(item.get("status")) == ScreenshotStatus.RE_REVIEW.value
    )
    deleted = sum(
        1 for item in dataset if str(item.get("status")) == ScreenshotStatus.DELETED.value
    )
    remaining = total - reviewed - deleted
    return {
        "total": total,
        "reviewed": reviewed,
        "deferred": deferred,
        "re_review": re_review,
        "deleted": deleted,
        "remaining": remaining,
    }


@router.get("/", response_model=PaginatedResponse)
def list_screenshots(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    filter: ScreenshotFilter = ScreenshotFilter.ALL,
    category: Optional[str] = None,
    search: Optional[str] = None,
    group_id: Optional[str] = None,
):
    try:
        dataset = load_screenshots()
        if category:
            dataset = [item for item in dataset if item.get("primary_category") == category]

        if filter == ScreenshotFilter.PENDING:
            dataset = [item for item in dataset if not (item.get("primary_category") or "").strip()]

        dataset = [item for item in dataset if _match_filter(item, filter_mode=filter)]

        if search:
            dataset = [item for item in dataset if _apply_search(item, search)]

        dataset.sort(
            key=lambda entry: _parse_datetime(entry.get("created_at"))
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        for item in dataset:
            item.setdefault("id", uuid4().hex)
            item["suggestions"] = _generate_suggestions(item)

        paginated_source, groups = _with_groups(dataset, group_id)

        total = len(paginated_source)
        total_pages = max((total - 1) // page_size + 1, 1)
        page = min(page, total_pages)
        page_items = _paginate(paginated_source, page, page_size)

        enriched_items = [_enrich_screenshot(item) for item in page_items]
        screenshots = [Screenshot.model_validate(enriched) for enriched in enriched_items]
        progress = _build_progress(load_screenshots())

        groups.current_index = min(groups.current_index, max(len(groups.items) - 1, 0))

        return PaginatedResponse(
            items=screenshots,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            progress=progress,
            groups=groups,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in list_screenshots")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{screenshot_id}", response_model=Screenshot)
def get_screenshot(screenshot_id: str):
    try:
        dataset = load_screenshots()
        for item in dataset:
            if item.get("id") == screenshot_id:
                item["suggestions"] = _generate_suggestions(item)
                enriched = _enrich_screenshot(item)
                return Screenshot.model_validate(enriched)
        raise HTTPException(status_code=404, detail="Screenshot not found")
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in get_screenshot")
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/{screenshot_id}", response_model=Screenshot)
def update_screenshot(screenshot_id: str, payload: ScreenshotUpdate):
    try:
        dataset = load_screenshots()
        updated_item = None
        for item in dataset:
            if item.get("id") == screenshot_id:
                update_data = payload.model_dump(exclude_unset=True)
                if isinstance(update_data.get("status"), ScreenshotStatus):
                    update_data["status"] = update_data["status"].value
                item.update(update_data)
                item["updated_at"] = datetime.now(timezone.utc).isoformat()
                updated_item = item
                break
        if not updated_item:
            raise HTTPException(status_code=404, detail="Screenshot not found")
        save_screenshots(dataset)
        updated_item["suggestions"] = _generate_suggestions(updated_item)
        enriched = _enrich_screenshot(updated_item)
        return Screenshot.model_validate(enriched)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in update_screenshot")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/batch", response_model=dict)
def batch_update(batch_request: BatchUpdateRequest):
    try:
        dataset = load_screenshots()
        id_set = set(batch_request.ids)
        if not id_set:
            raise HTTPException(status_code=400, detail="No screenshot ids provided")
        update_data = batch_request.payload.model_dump(exclude_unset=True)
        if isinstance(update_data.get("status"), ScreenshotStatus):
            update_data["status"] = update_data["status"].value
        if not update_data:
            raise HTTPException(status_code=400, detail="No updates provided")

        updated = 0
        timestamp = datetime.now(timezone.utc).isoformat()
        for item in dataset:
            if item.get("id") in id_set:
                item.update(update_data)
                item["updated_at"] = timestamp
                updated += 1
        if not updated:
            raise HTTPException(status_code=404, detail="No screenshots updated")
        save_screenshots(dataset)
        return {"updated": updated}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in batch_update")
        raise HTTPException(status_code=500, detail=str(exc))
