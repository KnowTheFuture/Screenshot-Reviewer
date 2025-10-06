"""Generate metadata for screenshot files in a directory."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


@dataclass
class ScreenshotEntry:
    id: str
    filename: str
    path: str
    created_at: str
    year: int
    year_month: str
    tags: List[str]
    notes: str
    processed: int
    file_hash: str | None = None

    def to_serializable(self, include_hash: bool) -> dict:
        data = asdict(self)
        data.pop("file_hash", None)
        if include_hash and self.file_hash:
            data["hash"] = self.file_hash
        return data


def iter_media_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def compute_file_hash(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def choose_timestamp(stat_result: os.stat_result) -> float:
    birthtime = getattr(stat_result, "st_birthtime", None)
    if birthtime is not None:
        return birthtime
    return stat_result.st_mtime


def format_timestamp(ts: float) -> tuple[str, int, str]:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    created_at = dt.isoformat().replace("+00:00", "Z")
    return created_at, dt.year, f"{dt.year}-{dt.month:02d}"


def build_entry(path: Path, skip_file_hash: bool) -> ScreenshotEntry:
    stat_result = path.stat()
    ts = choose_timestamp(stat_result)
    created_at, year, year_month = format_timestamp(ts)

    file_hash = None
    if not skip_file_hash:
        file_hash = compute_file_hash(path)
    entry_id_source = file_hash if file_hash else hashlib.sha1(str(path).encode("utf-8")).hexdigest()
    entry_id = f"sha1_{entry_id_source[:8]}"

    return ScreenshotEntry(
        id=entry_id,
        filename=path.name,
        path=str(path.resolve()),
        created_at=created_at,
        year=year,
        year_month=year_month,
        tags=[],
        notes="",
        processed=0,
        file_hash=file_hash,
    )


def generate_metadata(root: Path, include_hash: bool, skip_file_hash: bool) -> list[dict]:
    entries: list[ScreenshotEntry] = []
    for file_path in iter_media_files(root):
        entry = build_entry(path=file_path, skip_file_hash=skip_file_hash)
        entries.append(entry)

    entries.sort(key=lambda item: (item.created_at, item.filename))
    return [entry.to_serializable(include_hash=include_hash and not skip_file_hash) for entry in entries]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate metadata JSON for screenshots.")
    parser.add_argument(
        "source",
        nargs="?",
        default=Path.cwd(),
        type=Path,
        help="Directory to scan (defaults to current working directory).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("screenshots.json"),
        help="Output JSON file path (defaults to ./screenshots.json).",
    )
    parser.add_argument(
        "--skip-hash",
        action="store_true",
        help="Skip reading file contents for hashing (IDs fall back to path hash and no `hash` field is written).",
    )
    parser.add_argument(
        "--include-hash",
        action="store_true",
        help="Include the full SHA-1 hash in output (ignored when --skip-hash is set).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the JSON to stdout instead of writing to disk.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = args.source.expanduser().resolve()

    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"Source directory not found: {source_dir}")

    metadata = generate_metadata(
        root=source_dir,
        include_hash=args.include_hash,
        skip_file_hash=args.skip_hash,
    )

    if args.dry_run:
        json.dump(metadata, fp=os.sys.stdout, indent=2, ensure_ascii=False)
        if metadata:
            print()
        return

    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as outfile:
        json.dump(metadata, outfile, indent=2, ensure_ascii=False)

    print(f"Saved {len(metadata)} entries to {output_path}")


if __name__ == "__main__":
    main()
