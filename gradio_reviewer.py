"""Gradio-based reviewer UI for screenshot metadata enrichment."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

import gradio as gr


DATA_FILE = Path("screenshots.json")
LEXICON_DIR = Path("lexicon")
LEXICON_FILE = LEXICON_DIR / "tags.json"
CONF_THRESHOLD = 0.7


def load_json(path: Path) -> list | dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, payload: list | dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


if not DATA_FILE.exists():
    raise FileNotFoundError(f"Metadata file not found: {DATA_FILE}")

LEXICON_DIR.mkdir(parents=True, exist_ok=True)
if not LEXICON_FILE.exists():
    save_json(LEXICON_FILE, {})

data: list[dict] = load_json(DATA_FILE)
lexicon: dict[str, dict[str, list[str]]] = load_json(LEXICON_FILE)


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if not item:
            continue
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def compute_stats() -> str:
    total = len(data)
    reviewed = sum(1 for entry in data if entry.get("status") in {"processed", "reviewed"})
    deferred = sum(1 for entry in data if entry.get("status") == "deferred")
    rereview = sum(1 for entry in data if entry.get("status") == "re-review")
    low_conf = sum(1 for entry in data if entry.get("confidence", 0.0) < CONF_THRESHOLD)

    processed_pct = (reviewed / total * 100) if total else 0.0
    deferred_pct = (deferred / total * 100) if total else 0.0
    rereview_pct = (rereview / total * 100) if total else 0.0
    low_conf_pct = (low_conf / total * 100) if total else 0.0

    return (
        "\n".join(
            [
                "### 📊 Progress",
                f"• Reviewed: {reviewed}/{total} ({processed_pct:.1f}%)",
                f"• Deferred: {deferred}/{total} ({deferred_pct:.1f}%)",
                f"• Re-review: {rereview}/{total} ({rereview_pct:.1f}%)",
                f"• Low confidence: {low_conf}/{total} ({low_conf_pct:.1f}%)",
            ]
        )
    )


def resolve_image_path(entry: dict) -> str | None:
    raw = entry.get("path") or entry.get("filename")
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    return str(candidate) if candidate.exists() else raw


def get_filtered_indices(mode: str) -> list[int]:
    if mode == "Deferred only":
        return [idx for idx, entry in enumerate(data) if entry.get("status") == "deferred"]
    if mode == "Low confidence":
        return [idx for idx, entry in enumerate(data) if entry.get("confidence", 0.0) < CONF_THRESHOLD]
    if mode == "Re-review only":
        return [idx for idx, entry in enumerate(data) if entry.get("status") == "re-review"]
    return list(range(len(data)))


def suggest_tags(entry: dict) -> str:
    text = (entry.get("ocr_text") or "").lower()
    suggestions: set[str] = set()
    for key, info in lexicon.items():
        matches = info.get("match", [])
        aliases = [key] if not matches else matches
        for token in aliases:
            if token.lower() in text:
                for tag in info.get("tags", []):
                    if tag:
                        suggestions.add(tag)
                break
    return ", ".join(sorted(suggestions))


def entry_payload(filtered: List[int], position: int, mode: str, message: str = ""):
    stats_text = compute_stats()
    if not filtered:
        status_msg = message or f"⚠️ No entries match filter '{mode}'."
        return (
            None,
            "",
            "",
            "",
            0.0,
            status_msg,
            "",
            stats_text,
            0,
            filtered,
        )

    position = position % len(filtered)
    entry_index = filtered[position]
    entry = data[entry_index]

    tags_source = entry.get("tags") or entry.get("tags_ai") or []
    if isinstance(tags_source, str):
        tags_value = tags_source
    else:
        tags_value = ", ".join(tags_source)

    status_lines = []
    if message:
        status_lines.append(message)
    status_lines.append(
        f"📸 {entry_index + 1}/{len(data)} • Filter: {mode} • Status: {entry.get('status', 'pending')}"
    )
    reviewed_at = entry.get("reviewed_at") or entry.get("updated_at")
    if reviewed_at:
        status_lines.append(f"Last review: {reviewed_at}")

    return (
        resolve_image_path(entry),
        tags_value,
        entry.get("summary", ""),
        suggest_tags(entry),
        float(entry.get("confidence", 0.0) or 0.0),
        "\n".join(status_lines),
        entry.get("ocr_text", ""),
        stats_text,
        position,
        filtered,
    )


def update_entry(filtered: List[int], position: int, tags: str, summary: str, confidence: float) -> str:
    if not filtered:
        return "⚠️ Nothing to save."
    entry_index = filtered[position % len(filtered)]
    entry = data[entry_index]

    parsed_tags = [token.strip() for token in tags.split(",") if token.strip()]
    entry["tags"] = dedupe_preserve_order(parsed_tags)
    entry["summary"] = summary.strip()
    try:
        entry["confidence"] = float(confidence)
    except (TypeError, ValueError):
        entry["confidence"] = 0.0
    entry["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    entry["status"] = "reviewed"

    save_json(DATA_FILE, data)
    return f"✅ Saved entry {entry_index + 1}"


def next_entry(
    mode: str,
    filtered: List[int],
    position: int,
    save_flag: bool,
    tags: str,
    summary: str,
    confidence: float,
):
    filtered = filtered or get_filtered_indices(mode)
    message = ""
    if filtered and save_flag:
        message = update_entry(filtered, position, tags, summary, confidence)
    filtered = get_filtered_indices(mode)
    if not filtered:
        return entry_payload(filtered, 0, mode, message or "🎉 No remaining entries for this filter.")
    if position >= len(filtered):
        position = 0
    position = (position + 1) % len(filtered)
    return entry_payload(filtered, position, mode, message)


def prev_entry(mode: str, filtered: List[int], position: int):
    filtered = filtered or get_filtered_indices(mode)
    if not filtered:
        return entry_payload(filtered, 0, mode, "⚠️ No entries available.")
    position = (position - 1) % len(filtered)
    return entry_payload(filtered, position, mode)


def skip_entry(mode: str, filtered: List[int], position: int):
    filtered = filtered or get_filtered_indices(mode)
    if not filtered:
        return entry_payload(filtered, 0, mode, "⚠️ No entries to skip.")
    next_pos = (position + 1) % len(filtered)
    return entry_payload(filtered, next_pos, mode, "⏭️ Skipped current entry.")


def mark_re_review(mode: str, filtered: List[int], position: int):
    filtered = filtered or get_filtered_indices(mode)
    if not filtered:
        return entry_payload(filtered, 0, mode, "⚠️ No entries to mark.")

    entry_index = filtered[position % len(filtered)]
    entry = data[entry_index]
    entry["status"] = "re-review"
    entry["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    entry["marked_at"] = entry["reviewed_at"]
    save_json(DATA_FILE, data)

    filtered = get_filtered_indices(mode)
    if not filtered:
        return entry_payload(filtered, 0, mode, f"🔁 Marked entry {entry_index + 1} for re-review. Filter now empty.")
    position = position % len(filtered)
    return entry_payload(filtered, position, mode, f"🔁 Marked entry {entry_index + 1} for re-review.")


def add_to_lexicon(keyword: str, tags: str, filtered: List[int], position: int):
    keyword_clean = keyword.strip().lower()
    tags_clean = [token.strip() for token in tags.split(",") if token.strip()]
    if not keyword_clean or not tags_clean:
        return "⚠️ Provide both keyword and tags", suggest_current(filtered, position)

    lexicon[keyword_clean] = {
        "match": [keyword_clean],
        "tags": tags_clean,
    }
    save_json(LEXICON_FILE, lexicon)

    return (
        f"✅ Added '{keyword_clean}' to lexicon",
        suggest_current(filtered, position),
    )


def suggest_current(filtered: List[int], position: int) -> str:
    if not filtered:
        return ""
    entry_index = filtered[position % len(filtered)]
    entry = data[entry_index]
    return suggest_tags(entry)


def init_view(mode: str):
    filtered = get_filtered_indices(mode)
    return entry_payload(filtered, 0, mode)


with gr.Blocks(css=".keyhint {font-size: 0.9em; color: gray;}") as demo:
    gr.Markdown("## 🧠 Screenshot Reviewer + Lexicon Builder")

    with gr.Row():
        mode = gr.Dropdown(
            ["All", "Deferred only", "Low confidence", "Re-review only"],
            label="Filter Mode",
            value="Low confidence",
        )
        index_state = gr.State(0)
        filtered_state = gr.State([])

    with gr.Row():
        image = gr.Image(label="Screenshot", interactive=False)
        with gr.Column():
            tags_box = gr.Textbox(label="Tags (comma-separated)")
            summary_box = gr.Textbox(label="Summary", lines=4)
            confidence_slider = gr.Slider(0, 1, step=0.05, label="Confidence")
            suggestions_box = gr.Textbox(label="Suggested Tags", interactive=False)
            ocr_box = gr.Textbox(label="OCR / Context", interactive=False, lines=6)
            status_md = gr.Markdown()

    stats_md = gr.Markdown()

    with gr.Row():
        prev_btn = gr.Button("⬅️ Prev", elem_id="prev-btn")
        next_btn = gr.Button("➡️ Next (Save)", elem_id="next-btn")
        skip_btn = gr.Button("⏭️ Skip", elem_id="skip-btn")
        rereview_btn = gr.Button("🔁 Mark for Re-review", elem_id="rereview-btn")

    gr.Markdown(
        """
        <div class='keyhint'>
        ⌨️ Keyboard Shortcuts: ← Prev | → or Enter = Save & Next | s = Skip | r = Mark for Re-review
        </div>
        """
    )

    gr.Markdown("### ➕ Add to Lexicon")
    with gr.Row():
        new_keyword = gr.Textbox(label="Keyword (match trigger)")
        new_tags = gr.Textbox(label="Tags (comma-separated)")
        add_btn = gr.Button("Add")
    add_status = gr.Markdown()

    outputs = [
        image,
        tags_box,
        summary_box,
        suggestions_box,
        confidence_slider,
        status_md,
        ocr_box,
        stats_md,
        index_state,
        filtered_state,
    ]

    mode.change(init_view, inputs=[mode], outputs=outputs)
    demo.load(init_view, inputs=[mode], outputs=outputs)

    prev_btn.click(prev_entry, inputs=[mode, filtered_state, index_state], outputs=outputs)

    next_btn.click(
        next_entry,
        inputs=[mode, filtered_state, index_state, gr.State(True), tags_box, summary_box, confidence_slider],
        outputs=outputs,
    )

    skip_btn.click(skip_entry, inputs=[mode, filtered_state, index_state], outputs=outputs)

    rereview_btn.click(mark_re_review, inputs=[mode, filtered_state, index_state], outputs=outputs)

    add_btn.click(
        add_to_lexicon,
        inputs=[new_keyword, new_tags, filtered_state, index_state],
        outputs=[add_status, suggestions_box],
    )

    gr.HTML(
        """
        <script>
        document.addEventListener("keydown", function (event) {
            const active = document.activeElement;
            if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA")) {
                return;
            }
            if (event.key === "ArrowLeft") {
                const btn = document.getElementById("prev-btn");
                btn && btn.click();
            }
            if (event.key === "ArrowRight" || event.key === "Enter") {
                const btn = document.getElementById("next-btn");
                btn && btn.click();
            }
            if (event.key === "s" || event.key === "S") {
                const btn = document.getElementById("skip-btn");
                btn && btn.click();
            }
            if (event.key === "r" || event.key === "R") {
                const btn = document.getElementById("rereview-btn");
                btn && btn.click();
            }
        });
        </script>
        """
    )


if __name__ == "__main__":
    demo.launch()
