"""Utility script to seed the screenshot reviewer dataset with starter content."""

from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

try:
    from storage import (  # type: ignore
        load_categories,
        load_lexicon,
        load_screenshots,
        save_categories,
        save_lexicon,
        save_screenshots,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - defensive
    raise SystemExit(f"Unable to import storage helpers: {exc}")

DEFAULT_CATEGORIES = [
    "Gaming",
    "Coding",
    "Market Research",
    "Personal",
    "Work",
]

DEFAULT_LEXICON = [
    {"keyword": "skyrim", "tags": ["gaming", "rpg", "skyrim"]},
    {"keyword": "dashboard", "tags": ["analytics", "dashboard", "kpi"]},
    {"keyword": "jira", "tags": ["project", "tickets", "work"]},
]

SAMPLE_TAGS = {
    "Gaming": ["gaming", "screenshot", "walkthrough"],
    "Coding": ["code", "editor", "terminal"],
    "Market Research": ["survey", "charts", "insights"],
    "Personal": ["photo", "notes", "journal"],
    "Work": ["meeting", "slides", "project"],
}


def _ensure_categories() -> list[dict]:
    categories = load_categories()
    if categories:
        return categories
    seeded = []
    for name in DEFAULT_CATEGORIES:
        seeded.append(
            {
                "id": uuid4().hex,
                "name": name,
                "description": None,
                "created_at": datetime.utcnow().isoformat(),
            }
        )
    save_categories(seeded)
    return seeded


def _ensure_lexicon() -> list[dict]:
    lexicon = load_lexicon()
    if lexicon:
        return lexicon
    seeded = []
    for entry in DEFAULT_LEXICON:
        seeded.append(
            {
                "id": uuid4().hex,
                "keyword": entry["keyword"],
                "tags": entry["tags"],
                "created_at": datetime.utcnow().isoformat(),
            }
        )
    save_lexicon(seeded)
    return seeded


def _ensure_screenshots(categories: list[dict]) -> list[dict]:
    screenshots = load_screenshots()
    if screenshots:
        return screenshots
    seeded = []
    now = datetime.now(timezone.utc)
    for category in categories:
        for index in range(1, 4):
            captured = now - timedelta(minutes=random.randint(1, 5000))
            seeded.append(
                {
                    "id": uuid4().hex,
                    "path": f"sample/{category['name'].lower().replace(' ', '_')}_{index}.png",
                    "tags": SAMPLE_TAGS.get(category["name"], []),
                    "summary": f"Sample {category['name']} screenshot #{index}",
                    "primary_category": category["id"],
                    "status": "reviewed",
                    "confidence": round(random.uniform(0.4, 0.95), 2),
                    "ocr_text": f"Example content for {category['name']} #{index}",
                    "created_at": captured.isoformat(),
                    "updated_at": captured.isoformat(),
                }
            )
    save_screenshots(seeded)
    return seeded


def main() -> None:
    categories = _ensure_categories()
    _ensure_lexicon()
    _ensure_screenshots(categories)
    print("Seed data generated successfully.")


if __name__ == "__main__":
    main()
