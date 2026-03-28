from __future__ import annotations

from pathlib import Path


def load_score_preview(output_path: Path, max_chars: int = 4000) -> str:
    """Load exported score text content with a safe size cap for UI preview."""

    content = output_path.read_text(encoding="utf-8")
    if len(content) <= max_chars:
        return content
    return f"{content[:max_chars]}\n...（预览已截断）"