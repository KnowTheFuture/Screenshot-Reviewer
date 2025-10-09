# scripts/build_sample_screenshots_json.py
import json
from pathlib import Path
import uuid
import datetime

# Source folder containing the actual screenshots
SCREENSHOTS_DIR = Path("/Volumes/990_Pro/Screenshots")

# Destination file for sample output
DEST_FILE = Path("/Volumes/990_Pro/Screenshots/screenshot-reviewer/backend/data/screenshots.json")

# Collect up to 10 image files (recursive search)
image_files = [
    f for f in SCREENSHOTS_DIR.rglob("*")
    if f.suffix.lower() in (".png", ".jpg", ".jpeg")
][:10]

# Default category for now
CATEGORY_DEFAULT = "41941357919649358d762b8187fd5a96"

records = []
for img in image_files:
    records.append({
        "id": f"sha1_{uuid.uuid4().hex[:8]}",
        "path": str(img),
        "tags": [],
        "summary": "",
        "primary_category": CATEGORY_DEFAULT,
        "status": "pending",
        "confidence": 0.0,
        "ocr_text": "",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
    })

DEST_FILE.write_text(json.dumps(records, indent=2))
print(f"✅ Sample file written with {len(records)} screenshots → {DEST_FILE}")