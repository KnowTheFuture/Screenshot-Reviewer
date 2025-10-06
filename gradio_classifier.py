"""Gradio-based batch classifier for screenshot categories."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

import gradio as gr


DATA_FILE = Path("screenshots.json")
CATEGORY_FILE = Path("categories.json")
IMAGES_PER_PAGE = 50

DEFAULT_CATEGORIES = [
    "Gaming",
    "Coding",
    "Market Research",
    "Productivity",
    "UI/UX",
    "System",
    "Misc",
]


def save_json(path: Path, payload: list | dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def ensure_files() -> None:
    if not DATA_FILE.exists():
        save_json(DATA_FILE, [])
    if not CATEGORY_FILE.exists():
        save_json(CATEGORY_FILE, {"categories": DEFAULT_CATEGORIES})


def load_data() -> list[dict]:
    ensure_files()
    with DATA_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_data(records: list[dict]) -> None:
    save_json(DATA_FILE, records)


def load_categories() -> list[str]:
    ensure_files()
    with CATEGORY_FILE.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    categories = payload.get("categories", [])
    if not categories:
        categories = list(DEFAULT_CATEGORIES)
        save_categories(categories)
    return categories


def save_categories(categories: list[str]) -> None:
    save_json(CATEGORY_FILE, {"categories": categories})


data: list[dict] = load_data()
categories: list[str] = load_categories()


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        token = item.strip()
        if not token or token in seen:
            continue
        seen.add(token)
        ordered.append(token)
    return ordered


def resolve_image_path(entry: dict) -> str | None:
    raw = entry.get("path") or entry.get("filename")
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if candidate.exists():
        return str(candidate)
    return raw


def get_filter_options() -> list[str]:
    return ["Pending", "All", *categories]


def normalize_filter(selected: str) -> str:
    options = get_filter_options()
    if selected in options:
        return selected
    return options[0] if options else "All"


def filter_indices(filter_mode: str) -> list[int]:
    normalized = normalize_filter(filter_mode)
    if normalized == "All":
        return list(range(len(data)))
    if normalized == "Pending":
        return [
            idx
            for idx, entry in enumerate(data)
            if entry.get("status") not in {"reviewed", "deleted"}
        ]
    return [
        idx
        for idx, entry in enumerate(data)
        if entry.get("primary_category") == normalized
    ]


def paginate_data(page: int, filter_mode: str):
    filtered = filter_indices(filter_mode)
    total_filtered = len(filtered)
    if total_filtered == 0:
        return [], filtered, 0, 0, 0
    total_pages = math.ceil(total_filtered / IMAGES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * IMAGES_PER_PAGE
    end = start + IMAGES_PER_PAGE
    slice_indices = filtered[start:end]
    entries = []
    for idx in slice_indices:
        entry = data[idx]
        entries.append(
            {
                "index": idx,
                "path": entry.get("path") or entry.get("filename"),
                "resolved_path": resolve_image_path(entry),
                "status": entry.get("status", "pending"),
                "primary_category": entry.get("primary_category"),
            }
        )
    return entries, filtered, total_pages, total_filtered, page


def get_progress_summary() -> str:
    total = len(data)
    reviewed = sum(1 for entry in data if entry.get("status") == "reviewed")
    deleted = sum(1 for entry in data if entry.get("status") == "deleted")
    pending = total - reviewed - deleted
    by_category = {
        category: sum(1 for entry in data if entry.get("primary_category") == category)
        for category in categories
    }
    parts = [
        "### 📈 Progress",
        f"• Reviewed: {reviewed}/{total}",
        f"• Pending: {pending}/{total}",
        f"• Deleted: {deleted}/{total}",
    ]
    if categories:
        category_bits = ", ".join(f"{cat}: {count}" for cat, count in by_category.items())
        parts.append(f"• By category → {category_bits}")
    return "\n".join(parts)


def assign_category(selected_paths: list[str], category: str) -> int:
    if not category:
        return 0
    updated = 0
    category = category.strip()
    now_ts = datetime.now(timezone.utc).isoformat()
    for entry in data:
        path = entry.get("path") or entry.get("filename")
        if path in selected_paths:
            entry["primary_category"] = category
            entry["status"] = "reviewed"
            entry["reviewed_at"] = now_ts
            updated += 1
    if updated:
        save_data(data)
    return updated


def mark_for_deletion(selected_paths: list[str]) -> int:
    if not selected_paths:
        return 0
    updated = 0
    now_ts = datetime.now(timezone.utc).isoformat()
    for entry in data:
        path = entry.get("path") or entry.get("filename")
        if path in selected_paths:
            entry["status"] = "deleted"
            entry["primary_category"] = None
            entry["deleted_at"] = now_ts
            updated += 1
    if updated:
        save_data(data)
    return updated


def add_category(name: str) -> tuple[bool, str]:
    cleaned = name.strip()
    if not cleaned:
        return False, "⚠️ Provide a category name."
    if cleaned in categories:
        return False, f"⚠️ Category '{cleaned}' already exists."
    categories.append(cleaned)
    save_categories(categories)
    return True, f"✅ Added category '{cleaned}'."


def delete_category(name: str) -> tuple[bool, str]:
    cleaned = name.strip()
    if not cleaned:
        return False, "⚠️ Select a category to delete."
    if cleaned not in categories:
        return False, f"⚠️ Category '{cleaned}' not found."
    categories.remove(cleaned)
    for entry in data:
        if entry.get("primary_category") == cleaned:
            entry["primary_category"] = None
            if entry.get("status") == "reviewed":
                entry["status"] = "pending"
    save_categories(categories)
    save_data(data)
    return True, f"🗑️ Deleted category '{cleaned}'."


def rename_category(old_name: str, new_name: str) -> tuple[bool, str]:
    old_clean = old_name.strip()
    new_clean = new_name.strip()
    if not old_clean or not new_clean:
        return False, "⚠️ Provide both current and new names."
    if old_clean not in categories:
        return False, f"⚠️ Category '{old_clean}' not found."
    if new_clean in categories:
        return False, f"⚠️ Category '{new_clean}' already exists."
    idx = categories.index(old_clean)
    categories[idx] = new_clean
    for entry in data:
        if entry.get("primary_category") == old_clean:
            entry["primary_category"] = new_clean
    save_categories(categories)
    save_data(data)
    return True, f"✏️ Renamed '{old_clean}' → '{new_clean}'."


def render_page(filter_mode: str, page: int, message: str = ""):
    entries, filtered, total_pages, total_filtered, adjusted_page = paginate_data(page, filter_mode)
    gallery_items: list[tuple[str | None, str]] = []
    page_paths: list[str] = []
    for item in entries:
        caption_bits = [item.get("path", "<unknown>")]
        if item.get("primary_category"):
            caption_bits.append(f"[{item['primary_category']}]")
        if item.get("status") == "deleted":
            caption_bits.append("🗑️")
        gallery_items.append(
            (
                item.get("resolved_path") or item.get("path"),
                " ".join(caption_bits),
            )
        )
        if item.get("path"):
            page_paths.append(item["path"])

    checkbox_choices = page_paths
    if page_paths:
        status_text = message or "Select screenshots, then choose a category."
    else:
        status_text = message or f"⚠️ No entries for filter '{filter_mode}'."

    if total_filtered == 0:
        page_info = f"Page 0/0 • Showing 0 of 0"
    else:
        page_info = (
            f"Page {adjusted_page + 1}/{total_pages} • Showing {len(entries)} of {total_filtered}"
        )

    return (
        gr.Gallery.update(value=gallery_items, label="Screenshots"),
        gr.CheckboxGroup.update(choices=checkbox_choices, value=[]),
        status_text,
        get_progress_summary(),
        adjusted_page,
        page_paths,
        page_info,
    )


def handle_assign(category: str, selected: list[str] | None, page_paths: list[str], filter_mode: str, page: int):
    selected_set = set(selected or [])
    valid_selection = [path for path in page_paths if path in selected_set]
    if not valid_selection:
        return render_page(filter_mode, page, "⚠️ Select at least one screenshot.")
    if not category:
        return render_page(filter_mode, page, "⚠️ Choose a category to assign.")
    updated = assign_category(valid_selection, category)
    message = f"✅ Categorized {updated} screenshot(s) as '{category}'." if updated else "⚠️ Nothing updated."
    return render_page(filter_mode, page, message)


def handle_delete(selected: list[str] | None, page_paths: list[str], filter_mode: str, page: int):
    selected_set = set(selected or [])
    valid_selection = [path for path in page_paths if path in selected_set]
    if not valid_selection:
        return render_page(filter_mode, page, "⚠️ Select screenshots to delete.")
    updated = mark_for_deletion(valid_selection)
    message = f"🗑️ Marked {updated} screenshot(s) for deletion." if updated else "⚠️ Nothing updated."
    return render_page(filter_mode, page, message)


def change_page(filter_mode: str, page: int, direction: int):
    target_page = max(0, page + direction)
    return render_page(filter_mode, target_page)


def init_view(filter_mode: str):
    start_page = 0 if filter_mode == "Pending" else 0
    return render_page(filter_mode, start_page)


def update_filter_choices(current_filter: str):
    options = get_filter_options()
    normalized = normalize_filter(current_filter)
    if normalized not in options:
        normalized = options[0] if options else "All"
    return gr.Dropdown.update(choices=options, value=normalized)


with gr.Blocks(css=".keyhint {font-size: 0.9em; color: gray;}") as demo:
    gr.Markdown("## 🗂️ Screenshot Batch Classifier")

    with gr.Row():
        filter_dropdown = gr.Dropdown(
            get_filter_options(),
            label="Filter",
            value="Pending",
        )
        page_state = gr.State(0)
        page_paths_state = gr.State([])
        page_info_md = gr.Markdown()

    with gr.Row():
        gallery = gr.Gallery(label="Screenshots", show_label=True)
    selection_box = gr.CheckboxGroup(label="Selected screenshots", show_label=False)
    status_md = gr.Markdown()
    progress_md = gr.Markdown(get_progress_summary())

    with gr.Row():
        prev_btn = gr.Button("⬅️ Prev Page", elem_id="prev-page")
        next_btn = gr.Button("➡️ Next Page", elem_id="next-page")
        skip_btn = gr.Button("⏭️ Skip")

    with gr.Row():
        category_selector = gr.Dropdown(categories, label="Assign category")
        assign_btn = gr.Button("✅ Assign to Category")
        delete_btn = gr.Button("🗑️ Mark for Deletion")

    gr.Markdown(
        """
        <div class='keyhint'>Tips: select items with the checkboxes, choose a category, then click Assign. Use Skip to advance without changes.</div>
        """
    )

    gr.Markdown("### ✏️ Manage Categories")
    with gr.Row():
        category_input = gr.Textbox(label="New category")
        add_category_btn = gr.Button("Add")
    with gr.Row():
        manage_dropdown = gr.Dropdown(categories, label="Existing categories", interactive=True)
        rename_input = gr.Textbox(label="Rename to")
    with gr.Row():
        delete_category_btn = gr.Button("Delete")
        rename_category_btn = gr.Button("Rename")
    category_status = gr.Markdown()

    outputs_main = [gallery, selection_box, status_md, progress_md, page_state, page_paths_state, page_info_md]
    category_outputs = outputs_main + [category_input, category_selector, manage_dropdown, filter_dropdown, category_status, rename_input]

    filter_dropdown.change(init_view, inputs=[filter_dropdown], outputs=outputs_main)
    demo.load(init_view, inputs=[filter_dropdown], outputs=outputs_main)

    prev_btn.click(change_page, inputs=[filter_dropdown, page_state, gr.State(-1)], outputs=outputs_main)
    next_btn.click(change_page, inputs=[filter_dropdown, page_state, gr.State(1)], outputs=outputs_main)
    skip_btn.click(change_page, inputs=[filter_dropdown, page_state, gr.State(1)], outputs=outputs_main)

    assign_btn.click(
        handle_assign,
        inputs=[category_selector, selection_box, page_paths_state, filter_dropdown, page_state],
        outputs=outputs_main,
    )

    delete_btn.click(
        handle_delete,
        inputs=[selection_box, page_paths_state, filter_dropdown, page_state],
        outputs=outputs_main,
    )

    def handle_add(name: str, current_filter: str, page: int):
        success, message = add_category(name)
        normalized_filter = normalize_filter(current_filter)
        main_outputs = render_page(normalized_filter, page, message)
        latest_value = categories[-1] if categories else None
        category_update = gr.Dropdown.update(choices=categories, value=latest_value)
        manage_update = gr.Dropdown.update(choices=categories, value=latest_value)
        filter_update = update_filter_choices(normalized_filter)
        rename_update = gr.Textbox.update(value="")
        input_update = gr.Textbox.update(value="") if success else gr.Textbox.update()
        status_update = gr.Markdown.update(value=message)
        return (*main_outputs, input_update, category_update, manage_update, filter_update, status_update, rename_update)

    add_category_btn.click(
        handle_add,
        inputs=[category_input, filter_dropdown, page_state],
        outputs=category_outputs,
    )

    def handle_delete_category(selected: str, current_filter: str, page: int):
        success, message = delete_category(selected)
        normalized_filter = normalize_filter(current_filter)
        target_filter = normalized_filter
        target_page = page
        if success and normalized_filter == selected:
            target_filter = "Pending"
            target_page = 0
        main_outputs = render_page(target_filter, target_page, message)
        filter_update = update_filter_choices(target_filter)
        category_value = categories[0] if categories else None
        category_update = gr.Dropdown.update(choices=categories, value=category_value)
        manage_update = gr.Dropdown.update(choices=categories, value=category_value)
        rename_update = gr.Textbox.update(value="")
        input_update = gr.Textbox.update()
        status_update = gr.Markdown.update(value=message)
        return (*main_outputs, input_update, category_update, manage_update, filter_update, status_update, rename_update)

    delete_category_btn.click(
        handle_delete_category,
        inputs=[manage_dropdown, filter_dropdown, page_state],
        outputs=category_outputs,
    )

    def handle_rename_category(selected: str, new_name: str, current_filter: str, page: int):
        success, message = rename_category(selected, new_name)
        normalized_filter = normalize_filter(current_filter)
        main_outputs = render_page(normalized_filter, page, message)
        filter_update = update_filter_choices(normalized_filter)
        value = new_name if success else selected
        category_update = gr.Dropdown.update(choices=categories, value=value if categories else None)
        manage_update = gr.Dropdown.update(choices=categories, value=value if categories else None)
        rename_update = gr.Textbox.update(value="")
        input_update = gr.Textbox.update()
        status_update = gr.Markdown.update(value=message)
        return (*main_outputs, input_update, category_update, manage_update, filter_update, status_update, rename_update)

    rename_category_btn.click(
        handle_rename_category,
        inputs=[manage_dropdown, rename_input, filter_dropdown, page_state],
        outputs=category_outputs,
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
                document.getElementById("prev-page")?.click();
            }
            if (event.key === "ArrowRight") {
                document.getElementById("next-page")?.click();
            }
        });
        </script>
        """
    )


if __name__ == "__main__":
    demo.launch()
