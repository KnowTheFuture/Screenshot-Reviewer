"""Batch enrichment scaffold for screenshot metadata using Llama 3.2 via Ollama."""
# To ensure reproducible runtime:
# python3 -m venv .venv && source .venv/bin/activate
# pip install -r requirements.txt
from __future__ import annotations

import argparse
import json
import logging
import re
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta, timezone
from json import JSONDecodeError
from pathlib import Path
from typing import Any

YES_NO_QUESTIONS: list[tuple[str, str]] = [
    ("Is this screenshot related to work or productivity tools?", "work"),
    ("Does it feature communication or messaging apps?", "communication"),
    ("Is there visible code or a terminal window?", "development"),
    ("Is it a game or entertainment content?", "entertainment"),
    ("Does it include charts, dashboards, or analytics?", "analytics"),
]

BATCH_SIZE = 5
JSON_FILE = "screenshots.json"
MODEL = "llama3.2"
LOG_DIR_DEFAULT = Path("logs")

logger = logging.getLogger(__name__)


def load_metadata(file_path: Path) -> list[dict[str, Any]]:
    with file_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def build_prompt(batch: list[dict[str, Any]]) -> str:
    prompt_payload = []
    for item in batch:
        prompt_payload.append(
            {
                "filename": item.get("filename"),
                "created_at": item.get("created_at"),
                "year_month": item.get("year_month"),
                "ocr_text": item.get("ocr_text", ""),
            }
        )

    items_str = json.dumps(prompt_payload, indent=2, ensure_ascii=False)
    prompt = f"""
You are a tagging assistant.

Analyze each screenshot object below and output a JSON array of objects in the same order.

For each screenshot:
- Suggest 3–5 topical tags (project/game/tool, category, theme).
- Write a short one-sentence summary (notes).
- Include a confidence score (0–1).
- If you cannot classify or are uncertain, set "ask_user": true and leave "tags_ai" empty.

Input screenshots:
{items_str}

Return **only** JSON, in this structure:
[
  {{
    "filename": "...",
    "tags_ai": ["Tag1", "Tag2"],
    "summary": "...",
    "confidence": 0.93,
    "ask_user": false
  }},
  ...
]
""".strip()
    return prompt


class TimeoutExpired(Exception):
    """Raised when no input is received before the timeout expires."""


def _timeout_handler(signum, frame):  # pragma: no cover - signal handler
    raise TimeoutExpired


def timed_input(prompt: str, *, timeout: int, default: str) -> str:
    """Obtain input with a timeout, returning default on expiry."""
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(timeout)
    try:
        response = input(prompt).strip()
        signal.alarm(0)
    except TimeoutExpired:
        signal.alarm(0)
        print(f"\n⏱  Timeout reached → defaulting to {default!r}")
        response = default
    except Exception:
        signal.alarm(0)
        response = default
    return response or default


def prompt_menu(filename: str, confidence: float, *, timeout: int = 30, default_choice: str = "2") -> str:
    print(f"\n❓  {filename} (confidence {confidence:.2f})")
    file_path = Path(filename)
    try:
        resolved_path = file_path if file_path.is_absolute() else (Path.cwd() / file_path).resolve()
    except Exception:
        resolved_path = file_path
    print(f"🔗 file://{resolved_path}")
    print("[1] Skip for later")
    print("[2] Retry now with more context")
    print("[3] Manual fix")
    print(f"(⏱ Auto-select [{default_choice}] after {timeout}s of inactivity)")

    choice = timed_input("Choice: ", timeout=timeout, default=default_choice)
    action = {"1": "skip", "2": "retry", "3": "manual"}.get(choice, "retry")
    logger.info("Decision for %s: choice=%s → %s", filename, choice, action)
    return action


def build_retry_prompt(item: dict[str, Any], previous_result: dict[str, Any]) -> str:
    hint_tags = ", ".join(previous_result.get("tags_ai", []))
    return (
        "\n".join(
            [
                "You returned low confidence "
                f"({previous_result.get('confidence', 0)}) for:",
                json.dumps(item, indent=2, ensure_ascii=False),
                "",
                f"Previous tags: {hint_tags or 'None'}",
                "",
                "Try again and output a single JSON object with improved tags and summary.",
                "Return only JSON.",
            ]
        )
    ).strip()


def parse_iso_utc(dt_str: str) -> datetime:
    """Parse ISO 8601 string into UTC-aware datetime, fallback to datetime.min UTC."""
    if not dt_str:
        return datetime.min.replace(tzinfo=UTC)
    try:
        parsed = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=UTC)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def pending_entries(data: list[dict[str, Any]], *, reference: datetime | None = None) -> list[dict[str, Any]]:
    reference = reference or datetime.now(UTC)
    pending: list[dict[str, Any]] = []
    for entry in data:
        if entry.get("processed"):
            continue
        if entry.get("status") == "deferred":
            defer_until = parse_iso_utc(entry.get("defer_until", ""))
            if defer_until > reference:
                continue
        pending.append(entry)
    return pending


def write_log(log_dir: Path | None, log_id: str, suffix: str, content: str) -> None:
    if not log_dir:
        return
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    safe_id = "".join(c if c.isalnum() else "_" for c in log_id)[:32] or "batch"
    (log_dir / f"{timestamp}-{safe_id}.{suffix}").write_text(content, encoding="utf-8")


def write_batch_summary(
    log_dir: Path | None,
    *,
    filenames: list[str],
    processed: int,
    deferred: int,
    retried: int,
):
    if not log_dir:
        return
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    summary_path = log_dir / f"batch_{timestamp}.log"
    lines = [
        f"Processed: {processed}",
        f"Deferred: {deferred}",
        f"Retried: {retried}",
        "Files:",
        *[f"  - {name}" for name in filenames],
    ]
    summary_path.write_text("\n".join(lines), encoding="utf-8")


def _extract_json_block(text: str):
    """Locate and parse the first viable JSON block within the text."""
    match = re.search(r"[\[{]", text)
    if not match:
        return {"ask_user": True}
    start = match.start()
    decoder = json.JSONDecoder()
    for end in range(len(text), start, -1):
        snippet = text[start:end]
        try:
            parsed, _ = decoder.raw_decode(snippet)
        except JSONDecodeError:
            continue
        return parsed
    return {"ask_user": True}


def isoformat_utc(dt: datetime) -> str:
    """Return an ISO 8601 string in UTC with trailing Z."""
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def sanitize_defer_timestamps(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ensure legacy defer_until values are UTC-aware."""
    changed = 0
    for entry in data:
        ts = entry.get("defer_until")
        if not ts:
            continue
        parsed = parse_iso_utc(ts)
        normalized = isoformat_utc(parsed)
        if ts != normalized:
            entry["defer_until"] = normalized
            changed += 1
    if changed:
        print(f"Sanitized {changed} defer_until timestamps")
    return data


def group_by_time(entries: list[dict[str, Any]], window: int = 30) -> list[list[dict[str, Any]]]:
    """Group screenshots captured within `window` seconds of each other."""
    if not entries:
        return []
    sorted_entries = sorted(entries, key=lambda e: e.get("created_at") or "")
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    orphans: list[dict[str, Any]] = []
    last_ts: datetime | None = None

    for entry in sorted_entries:
        ts_raw = entry.get("created_at")
        if not ts_raw:
            orphans.append(entry)
            continue
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            orphans.append(entry)
            continue

        if last_ts and (ts - last_ts).total_seconds() > window:
            if current:
                groups.append(current)
                current = []
        current.append(entry)
        last_ts = ts

    if current:
        groups.append(current)

    if orphans:
        groups.append(orphans)

    return groups


def find_similar_entries(
    target: dict[str, Any],
    data: list[dict[str, Any]],
    window_minutes: int = 5,
) -> list[dict[str, Any]]:
    """Return entries captured within ±window_minutes of the target timestamp."""
    timestamp = target.get("created_at") or target.get("created")
    if not timestamp:
        return []
    try:
        t0 = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except Exception:
        return []
    start = t0 - timedelta(minutes=window_minutes)
    end = t0 + timedelta(minutes=window_minutes)
    similar: list[dict[str, Any]] = []
    for entry in data:
        if entry is target:
            continue
        ts = entry.get("created_at") or entry.get("created")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            continue
        if start <= dt <= end:
            similar.append(entry)
    return similar


def build_batches(entries: list[dict[str, Any]], batch_size: int, window: int = 30) -> list[list[dict[str, Any]]]:
    """Create batches respecting time grouping and batch size."""
    batches: list[list[dict[str, Any]]] = []
    for group in group_by_time(entries, window=window):
        chunk = list(group)
        while chunk:
            batches.append(chunk[:batch_size])
            chunk = chunk[batch_size:]
    return batches


def call_llama(
    prompt: str,
    *,
    model: str,
    log_dir: Path | None,
    log_id: str,
    expect_list: bool = True,
) -> Any:
    process = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode("utf-8"),
        capture_output=True,
        check=False,
    )

    stdout_text = process.stdout.decode("utf-8", errors="replace")
    stderr_text = process.stderr.decode("utf-8", errors="replace")

    write_log(log_dir, log_id, "prompt.txt", prompt)
    write_log(log_dir, log_id, "stdout.txt", stdout_text)
    if stderr_text:
        write_log(log_dir, log_id, "stderr.txt", stderr_text)

    if process.returncode != 0:
        print(stderr_text or stdout_text, file=sys.stderr)
        raise RuntimeError(f"ollama exited with code {process.returncode}")

    parsed = _extract_json_block(stdout_text)

    if expect_list:
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            result = dict(parsed)
            if result.get("ask_user") and "confidence" not in result:
                result["confidence"] = 0
            logger.warning(
                "Expected list response from Llama but received %s; wrapping in list",
                type(parsed).__name__,
            )
            return [result]
        logger.warning("Unable to parse Llama response into list; defaulting to ask_user fallback")
        return [{"ask_user": True, "confidence": 0}]

    # expect single object (retry path)
    if isinstance(parsed, dict):
        result = dict(parsed)
        if result.get("ask_user") and "confidence" not in result:
            result["confidence"] = 0
        return result

    if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
        return parsed[0]

    logger.warning("Retry response not parsed as JSON object; marking for manual review")
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        failure_path = log_dir / f"retry_failed_{time.strftime('%Y%m%d-%H%M%S')}.txt"
        failure_path.write_text(stdout_text, encoding="utf-8")
    return {"ask_user": True, "confidence": 0}


def save_metadata(file_path: Path, data: list[dict[str, Any]]) -> None:
    with file_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def update_master(data: list[dict[str, Any]], batch: list[dict[str, Any]]) -> None:
    lookup = {item["filename"]: item for item in batch if item.get("filename")}
    for idx, entry in enumerate(data):
        filename = entry.get("filename")
        if filename in lookup:
            data[idx] = lookup[filename]


def enrich_batches(
    *,
    data: list[dict[str, Any]],
    json_path: Path,
    batch_size: int,
    model: str,
    sleep_seconds: float,
    interactive: bool,
    log_dir: Path | None,
    confidence_threshold: float,
    defer_hours: float,
    auto: bool,
    confirm: bool,
    progress: dict[str, int],
    initial_unprocessed: list[dict[str, Any]] | None = None,
) -> None:
    unprocessed = initial_unprocessed if initial_unprocessed is not None else pending_entries(data)
    total = progress.setdefault("total", len(data))
    progress.setdefault("processed", 0)
    progress.setdefault("deferred", 0)
    print(f"{len(unprocessed)} screenshots pending")

    while unprocessed:
        grouped_batches = build_batches(unprocessed, batch_size)
        if not grouped_batches:
            break
        batch = grouped_batches[0]

        batch_processed = 0
        batch_deferred = 0
        batch_retried = 0
        prompt = build_prompt(batch)
        log_id = batch[0].get("filename", "batch")
        llama_results = call_llama(
            prompt,
            model=model,
            log_dir=log_dir,
            log_id=log_id,
            expect_list=True,
        )

        if isinstance(llama_results, dict):
            llama_results = [llama_results]
        elif isinstance(llama_results, str):
            logger.warning("⚠️ Llama returned string instead of JSON list: %r", llama_results)
            llama_results = []
        elif not isinstance(llama_results, list):
            logger.warning(
                "⚠️ Unexpected Llama output type for batch %s: %s",
                log_id,
                type(llama_results).__name__,
            )
            llama_results = []

        if len(batch) != len(llama_results):
            logger.warning(
                "Expected %s results but received %s from Llama",
                len(batch),
                len(llama_results),
            )
            aligned_results: list[Any] = [None] * len(batch)
            limit = min(len(batch), len(llama_results))
            for idx in range(limit):
                aligned_results[idx] = llama_results[idx]
            if len(llama_results) < len(batch):
                defer_time = datetime.now(UTC) + timedelta(hours=defer_hours)
                defer_iso = isoformat_utc(defer_time)
                for item in batch[len(llama_results):]:
                    item.update(
                        {
                            "status": "deferred",
                            "defer_until": defer_iso,
                            "processed": 0,
                        }
                    )
                    batch_deferred += 1
                    logger.warning("Deferred %s due to missing Llama result", item.get("filename"))
            llama_results = aligned_results

        bad_response_log = Path("logs") / "bad_responses.jsonl"

        for index, item in enumerate(batch):
            result = llama_results[index] if index < len(llama_results) else None
            filename = item.get("filename", "<unknown>")
            if result is None:
                defer_until = datetime.now(UTC) + timedelta(hours=defer_hours)
                defer_iso = isoformat_utc(defer_until)
                item.update(
                    {
                        "status": "deferred",
                        "defer_until": defer_iso,
                        "processed": 0,
                        "confidence": 0,
                    }
                )
                batch_deferred += 1
                logger.warning("Deferred %s because result payload was missing", filename)
                continue

            if not isinstance(result, dict):
                logger.warning(
                    "⚠️ Llama returned non-dict result for index %s (%s): %r — skipping",
                    index,
                    filename,
                    result,
                )
                try:
                    bad_response_log.parent.mkdir(parents=True, exist_ok=True)
                    with bad_response_log.open("a", encoding="utf-8") as fh:
                        fh.write(
                            json.dumps(
                                {
                                    "timestamp": datetime.now(UTC).isoformat(),
                                    "index": index,
                                    "filename": filename,
                                    "output": repr(result),
                                }
                            )
                            + "\n"
                        )
                except OSError as exc:
                    logger.warning("Failed to record bad response: %s", exc)
                result = {"tags_ai": [], "summary": "", "confidence": 0, "status": "deferred"}

            try:
                confidence = float(result.get("confidence", 0) or 0)
            except Exception:  # pragma: no cover - defensive branch
                confidence = 0.0
                logger.warning(
                    "⚠️ Could not parse confidence for index %s (%s): %r",
                    index,
                    filename,
                    result,
                )

            item["llama_result"] = result
            item["confidence"] = confidence
            needs_attention = result.get("ask_user") or confidence < confidence_threshold

            if needs_attention:
                if interactive:
                    action = prompt_menu(filename, confidence)
                else:
                    action = "skip"
                    logger.info(
                        "Non-interactive mode: auto-skip %s (confidence %.2f)",
                        filename,
                        confidence,
                    )

                if action == "skip":
                    defer_until = datetime.now(UTC) + timedelta(hours=defer_hours)
                    defer_iso = isoformat_utc(defer_until)
                    item.update(
                        {
                            "status": "deferred",
                            "defer_until": defer_iso,
                            "processed": 0,
                            "confidence": confidence,
                        }
                    )
                    item.pop("ask_user", None)
                    batch_deferred += 1
                    print(f"⏳ Deferred {filename} until {defer_iso}")
                    logger.info("Deferred %s by user choice (confidence %.2f)", filename, confidence)
                    continue

                suggested_tags: list[str] = []
                similar_entries: list[dict[str, Any]] = []

                if action == "retry":
                    if interactive:
                        similar_entries = find_similar_entries(item, data)
                        if similar_entries:
                            print("🧭 Nearby screenshots for context:")
                            for neighbor in similar_entries[:5]:
                                neighbor_tags = neighbor.get("tags_ai") or neighbor.get("tags") or []
                                neighbor_conf = neighbor.get("confidence")
                                conf_display = (
                                    f"{neighbor_conf:.2f}" if isinstance(neighbor_conf, (int, float)) else "n/a"
                                )
                                print(
                                    f"   - {neighbor.get('filename', '<unknown>')} → "
                                    f"tags: {', '.join(neighbor_tags) or '—'} (conf {conf_display})"
                                )
                        suggested_tags = sorted(
                            {
                                tag
                                for entry in similar_entries
                                for tag in entry.get("tags_ai", [])
                                if tag
                            }
                        )
                        if suggested_tags:
                            print(f"💡 Suggested tags: {', '.join(suggested_tags)}")

                    confirm_retry = "y"
                    if interactive:
                        confirm_retry = timed_input(
                            "Retry with these hints? (y/n) [y]: ",
                            timeout=30,
                            default="y",
                        )

                    if confirm_retry.lower().startswith("y"):
                        retry_prompt = build_retry_prompt(item, result)
                        try:
                            retry_log_id = f"{log_id}-retry-{index}"
                            retry_response = call_llama(
                                retry_prompt,
                                model=model,
                                log_dir=log_dir,
                                log_id=retry_log_id,
                                expect_list=False,
                            )
                            if isinstance(retry_response, list) and retry_response:
                                retry_response = retry_response[0]
                            if not isinstance(retry_response, dict):
                                raise ValueError("Retry response was not a JSON object")

                            item.update(
                                {
                                    "tags_ai": retry_response.get("tags_ai", []),
                                    "summary": retry_response.get("summary", ""),
                                    "confidence": retry_response.get("confidence", confidence),
                                    "processed": 1,
                                    "status": "processed",
                                }
                            )
                            item.pop("ask_user", None)
                            item.pop("defer_until", None)
                            batch_retried += 1
                            batch_processed += 1
                            print(f"🔁 Retried {filename} (conf {item['confidence']:.2f})")
                            logger.info(
                                "Retry succeeded for %s with confidence %.2f",
                                filename,
                                item["confidence"],
                            )
                            continue
                        except Exception as exc:  # pragma: no cover - diagnostic path
                            print(f"⚠️ Retry failed: {exc} — falling back to manual")
                            logger.warning("Retry failed for %s: %s", filename, exc)
                    else:
                        logger.info("Retry skipped for %s after user declined", filename)
                    action = "manual"

                if action == "manual":
                    if not suggested_tags:
                        similar_entries = similar_entries or find_similar_entries(item, data)
                        suggested_tags = sorted(
                            {
                                tag
                                for entry in similar_entries
                                for tag in entry.get("tags_ai", [])
                                if tag
                            }
                        )
                    include_suggested = False
                    if suggested_tags:
                        print(f"💡 Nearby suggested tags: {', '.join(suggested_tags)}")
                        if interactive:
                            include_suggested = timed_input(
                                "Include suggested tags? (y/n) [y]: ",
                                timeout=30,
                                default="y",
                            ).lower().startswith("y")
                    print(f"✏️  Manual entry for {filename}")
                    guided_tags: list[str] = []
                    if interactive:
                        print("🧭 Quick guided questions (y/n):")
                        for question, candidate_tag in YES_NO_QUESTIONS:
                            answer = timed_input(
                                f" - {question} ",
                                timeout=30,
                                default="n",
                            ).lower()
                            if answer.startswith("y"):
                                guided_tags.append(candidate_tag)
                    additional_tags: list[str] = []
                    if interactive:
                        additional_tags_input = input("Enter additional tags (comma-separated, optional): ").strip()
                        additional_tags = [
                            tag.strip()
                            for tag in additional_tags_input.split(",")
                            if additional_tags_input and tag.strip()
                        ]
                    final_tags: list[str] = []
                    selected_suggestions = suggested_tags if include_suggested else []
                    for tag in [*guided_tags, *selected_suggestions, *additional_tags]:
                        if tag and tag not in final_tags:
                            final_tags.append(tag)
                    summary_text = input("Enter summary: ").strip()
                    item.update(
                        {
                            "tags_ai": final_tags,
                            "summary": summary_text,
                            "confidence": 1.0 if final_tags or summary_text else confidence,
                            "processed": 1,
                            "status": "processed",
                        }
                    )
                    item.pop("ask_user", None)
                    item.pop("defer_until", None)
                    batch_processed += 1
                    logger.info("Manual tagging completed for %s with tags=%s", filename, final_tags)
                    continue

            item.update(
                {
                    "tags_ai": result.get("tags_ai", []),
                    "summary": result.get("summary", ""),
                    "confidence": confidence,
                    "processed": 1,
                    "status": "processed",
                }
            )
            item.pop("ask_user", None)
            item.pop("defer_until", None)
            batch_processed += 1

        update_master(data, batch)

        save_metadata(json_path, data)
        print(f"✅ Processed {len(batch)} screenshots. Saved progress.")

        write_batch_summary(
            log_dir,
            filenames=[entry.get("filename", "<unknown>") for entry in batch],
            processed=batch_processed,
            deferred=batch_deferred,
            retried=batch_retried,
        )

        progress["processed"] = sum(1 for entry in data if entry.get("status") == "processed")
        progress["deferred"] = sum(1 for entry in data if entry.get("status") == "deferred")
        processed_total = progress["processed"]
        deferred_total = progress["deferred"]
        remaining = max(total - processed_total - deferred_total, 0)

        pct_processed = (processed_total / total * 100) if total else 0
        pct_deferred = (deferred_total / total * 100) if total else 0
        batch_total = batch_processed + batch_deferred
        pct_batch_proc = (batch_processed / batch_total * 100) if batch_total else 0
        pct_batch_def = (batch_deferred / batch_total * 100) if batch_total else 0

        print(
            "\n📊 Progress update:"\
            f"\n   ✅ Total processed: {processed_total}/{total} ({pct_processed:.1f}%)"\
            f"\n   ⏳ Deferred: {deferred_total}/{total} ({pct_deferred:.1f}%)"\
            f"\n   🧮 Remaining: {remaining}"
        )
        print(
            "   🔁 This batch → "
            f"{batch_processed} processed ({pct_batch_proc:.1f}%) | "
            f"{batch_deferred} deferred ({pct_batch_def:.1f}%)"
        )

        unprocessed = pending_entries(data)

        if interactive and confirm and unprocessed:
            cont = input("Continue with next batch? (y/n): ")
            if cont.strip().lower() != "y":
                break

        if sleep_seconds > 0 and unprocessed:
            time.sleep(sleep_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch enrich screenshot metadata with Llama 3.2")
    parser.add_argument(
        "--json-file",
        type=Path,
        default=Path(JSON_FILE),
        help="Path to screenshots JSON file",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help="Number of screenshots per batch",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=MODEL,
        help="Ollama model name to use",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=2.0,
        help="Seconds to sleep between batches",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.6,
        help="Minimum confidence before asking or deferring",
    )
    parser.add_argument(
        "--defer-hours",
        type=float,
        default=12,
        help="Hours to wait before reprocessing deferred items",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive menu; auto-skip low-confidence",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically continue through all batches without prompting",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Process all batches without asking to continue",
    )
    parser.add_argument(
        "--no-logs",
        action="store_true",
        help="Disable logging of prompts and outputs",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    json_path = args.json_file.expanduser().resolve()

    if not json_path.exists():
        raise SystemExit(f"JSON file not found: {json_path}")

    log_dir: Path | None = None if args.no_logs else LOG_DIR_DEFAULT

    data = load_metadata(json_path)
    data = sanitize_defer_timestamps(data)
    total_items = len(data)
    processed_items = sum(1 for entry in data if entry.get("status") == "processed")
    deferred_items = sum(1 for entry in data if entry.get("status") == "deferred")
    remaining_items = max(total_items - processed_items - deferred_items, 0)
    start_time = datetime.now(timezone.utc).isoformat()
    print(
        f"\n📈 Starting enrichment ({start_time})"
        f"\n   Total: {total_items} | Processed: {processed_items} | Deferred: {deferred_items} | Remaining: {remaining_items}"
    )

    progress = {
        "total": total_items,
        "processed": processed_items,
        "deferred": deferred_items,
    }

    now = datetime.now(UTC)

    def is_ready(entry: dict[str, Any]) -> bool:
        if entry.get("processed") != 0:
            return False
        if entry.get("status") != "deferred":
            return True
        ready_at = parse_iso_utc(entry.get("defer_until"))
        return ready_at <= now

    initial_unprocessed = [entry for entry in data if is_ready(entry)]
    confirm_batches = not args.no_confirm and not args.auto
    try:
        enrich_batches(
            data=data,
            json_path=json_path,
            batch_size=args.batch_size,
            model=args.model,
            sleep_seconds=args.sleep,
            interactive=not args.no_interactive,
            log_dir=log_dir,
            confidence_threshold=args.confidence_threshold,
            defer_hours=args.defer_hours,
            auto=args.auto,
            confirm=confirm_batches,
            progress=progress,
            initial_unprocessed=initial_unprocessed,
        )
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user. Saving progress before exit...")
        save_metadata(json_path, data)
        sys.exit(0)

    final_processed = progress.get("processed", processed_items)
    final_deferred = progress.get("deferred", deferred_items)
    final_remaining = max(total_items - final_processed - final_deferred, 0)
    print(
        "\n✅ Enrichment run complete"
        f"\n   Total processed: {final_processed}/{total_items}"
        f" | Deferred: {final_deferred}/{total_items}"
        f" | Remaining: {final_remaining}"
    )


if __name__ == "__main__":
    main()
