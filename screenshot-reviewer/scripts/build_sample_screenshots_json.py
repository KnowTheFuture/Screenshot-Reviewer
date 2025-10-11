# scripts/build_sample_screenshots_json.py
import json
import uuid
import datetime
from pathlib import Path
import argparse

# --- Config ---
SCREENSHOTS_DIR = Path("/Volumes/990_Pro/Screenshots")
DEST_FILE = Path("/Volumes/990_Pro/Screenshots/screenshot-reviewer/backend/data/screenshots.json")

# --- Argument Parser for batch size ---
parser = argparse.ArgumentParser(description="Add new screenshots to screenshots.json safely.")
parser.add_argument("--batch", type=int, default=25, help="Number of new screenshots to add (default: 25)")
args = parser.parse_args()
batch_size = args.batch

# --- Load existing data if available ---
if DEST_FILE.exists():
    existing = json.loads(DEST_FILE.read_text())
else:
    existing = []

existing_paths = {rec["path"] for rec in existing}

# --- Collect new image files (skip duplicates) ---
image_files = [
    f for f in SCREENSHOTS_DIR.rglob("*")
    if f.suffix.lower() in (".png", ".jpg", ".jpeg") and str(f) not in existing_paths
][:batch_size]

new_records = []
for img in image_files:
    new_records.append({
        "id": f"sha1_{uuid.uuid4().hex[:8]}",
        "path": str(img),
        "tags": [],
        "summary": "",
        "primary_category": "pending",  # ⬅️ not assigned yet
        "status": "pending",
        "confidence": 0.0,
        "ocr_text": "",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
    })

# --- Clean existing data if needed ---
for rec in existing:
    if rec.get("status") == "pending" and not rec.get("primary_category"):
        rec["primary_category"] = "pending"

combined = existing + new_records

# --- Write combined file ---
DEST_FILE.write_text(json.dumps(combined, indent=2))

print(f"✅ Added {len(new_records)} new screenshots (total: {len(combined)}) → {DEST_FILE}")