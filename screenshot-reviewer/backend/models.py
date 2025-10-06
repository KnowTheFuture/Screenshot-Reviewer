"""Pydantic models shared across the Screenshot Reviewer backend."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ScreenshotStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    DEFERRED = "deferred"
    RE_REVIEW = "re-review"
    DELETED = "deleted"


class Screenshot(BaseModel):
    id: str
    path: str
    tags: List[str] = Field(default_factory=list)
    summary: str = ""
    primary_category: Optional[str] = None
    status: ScreenshotStatus = ScreenshotStatus.PENDING
    confidence: float = 0.0
    ocr_text: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    defer_until: Optional[datetime] = None
    group_id: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)


class ScreenshotUpdate(BaseModel):
    path: Optional[str] = None
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    primary_category: Optional[str] = None
    status: Optional[ScreenshotStatus] = None
    confidence: Optional[float] = None
    ocr_text: Optional[str] = None
    created_at: Optional[datetime] = None
    defer_until: Optional[datetime] = None
    suggestions: Optional[List[str]] = None


class BatchUpdateRequest(BaseModel):
    ids: List[str]
    payload: ScreenshotUpdate


class Category(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    count: int = 0
    pending: int = 0


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class LexiconEntry(BaseModel):
    id: str
    keyword: str
    tags: List[str] = Field(default_factory=list)
    created_at: datetime


class LexiconCreate(BaseModel):
    keyword: str
    tags: List[str]


class PaginatedResponse(BaseModel):
    items: List[Screenshot]
    page: int
    page_size: int
    total: int
    total_pages: int
    progress: dict
    groups: "GroupsPayload"


class ScreenshotFilter(str, Enum):
    ALL = "all"
    PENDING = "pending"
    DEFERRED = "deferred"
    LOW_CONFIDENCE = "low-confidence"
    RE_REVIEW = "re-review"


class GroupSummary(BaseModel):
    group_id: str
    size: int
    start: Optional[datetime]
    end: Optional[datetime]


class GroupsPayload(BaseModel):
    items: List[GroupSummary]
    current_index: int = 0


PaginatedResponse.model_rebuild()
