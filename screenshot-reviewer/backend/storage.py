"""Persistence layer helpers for reading and writing JSON datasets."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Callable, Iterable, List

from fastapi import HTTPException

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

_SCREENSHOTS_FILE = DATA_DIR / "screenshots.json"
_CATEGORIES_FILE = DATA_DIR / "categories.json"
_LEXICON_FILE = DATA_DIR / "lexicon.json"

_LOCK = threading.Lock()


def _atomic_write(path: Path, payload: Any) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    tmp_path.replace(path)


def _ensure_files() -> None:
    for file in (_SCREENSHOTS_FILE, _CATEGORIES_FILE, _LEXICON_FILE):
        if not file.exists():
            file.write_text("[]\n", encoding="utf-8")


_ensure_files()


def load_screenshots() -> List[dict]:
    with _SCREENSHOTS_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_screenshots(dataset: Iterable[dict]) -> None:
    with _LOCK:
        _atomic_write(_SCREENSHOTS_FILE, list(dataset))


def load_categories() -> List[dict]:
    with _CATEGORIES_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_categories(dataset: Iterable[dict]) -> None:
    with _LOCK:
        _atomic_write(_CATEGORIES_FILE, list(dataset))


def load_lexicon() -> List[dict]:
    with _LEXICON_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_lexicon(dataset: Iterable[dict]) -> None:
    with _LOCK:
        _atomic_write(_LEXICON_FILE, list(dataset))


def get_item_or_404(dataset: List[dict], item_id: str, *, entity: str) -> dict:
    for item in dataset:
        if item.get("id") == item_id:
            return item
    raise HTTPException(status_code=404, detail=f"{entity} not found")
