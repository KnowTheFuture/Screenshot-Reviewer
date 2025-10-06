"""Routes for lexicon CRUD operations."""

from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from ..models import LexiconCreate, LexiconEntry
from ..storage import get_item_or_404, load_lexicon, save_lexicon

router = APIRouter()


@router.get("/", response_model=List[LexiconEntry])
def list_entries():
    entries = load_lexicon()
    normalized = []
    for entry in entries:
        created_at = entry.get("created_at") or datetime.utcnow().isoformat()
        normalized.append(
            LexiconEntry.model_validate(
                {
                    "id": entry.get("id", uuid4().hex),
                    "keyword": entry.get("keyword", ""),
                    "tags": entry.get("tags", []),
                    "created_at": created_at,
                }
            )
        )
    return normalized


@router.post("/", response_model=LexiconEntry, status_code=201)
def create_entry(payload: LexiconCreate):
    entries = load_lexicon()
    keyword = payload.keyword.strip().lower()
    if any(entry.get("keyword", "").lower() == keyword for entry in entries):
        raise HTTPException(status_code=409, detail="Keyword already exists")
    entry = {
        "id": uuid4().hex,
        "keyword": payload.keyword.strip(),
        "tags": payload.tags,
        "created_at": datetime.utcnow().isoformat(),
    }
    entries.append(entry)
    save_lexicon(entries)
    return LexiconEntry.model_validate(entry)


@router.delete("/{entry_id}", response_model=dict)
def delete_entry(entry_id: str):
    entries = load_lexicon()
    get_item_or_404(entries, entry_id, entity="Lexicon entry")
    entries = [entry for entry in entries if entry.get("id") != entry_id]
    save_lexicon(entries)
    return {"deleted": entry_id}
