# scripts/convert_screenshots.py
import json, uuid, datetime
from pathlib import Path

source = Path("/Volumes/990_Pro/Screenshots/screenshots.json")
dest = Path("/Volumes/990_Pro/Screenshots/screenshot-reviewer/backend/data/screenshots.json")

CATEGORY_DEFAULT = "41941357919649358d762b8187fd5a96"  # Gaming, for now

data = json.loads(source.read_text())
out = []

for s in data:
    out.append({
        "id": s.get("id") or f"sha1_{uuid.uuid4().hex[:8]}",
        "path": s["path"],
        "tags": s.get("tags", []) + s.get("tags_ai", []),
        "summary": s.get("summary", ""),
        "primary_category": CATEGORY_DEFAULT,
        "status": s.get("status", "pending"),
        "confidence": float(s.get("confidence", 0)),
        "ocr_text": s.get("notes", ""),
        "created_at": s.get("created_at") or datetime.datetime.utcnow().isoformat() + "Z",
        "updated_at": s.get("reviewed_at") or datetime.datetime.utcnow().isoformat() + "Z",
    })

dest.write_text(json.dumps(out, indent=2))
print(f"✅ Converted {len(out)} records to {dest}")