from __future__ import annotations

from pathlib import Path


def load_score_preview(
    output_path: Path,
    max_chars: int = 4000,
    truncated_suffix: str = "...（预览已截断）",
) -> str:
    """Load exported score text content with a safe size cap for UI preview."""

    with output_path.open("r", encoding="utf-8") as file_obj:
        preview = file_obj.read(max_chars + 1)

    if len(preview) <= max_chars:
        return preview
    return f"{preview[:max_chars]}\n{truncated_suffix}"