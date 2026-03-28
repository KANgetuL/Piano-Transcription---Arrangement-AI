from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(slots=True)
class UiSettings:
    export_format: str = "txt"
    export_dir: str = "./outputs"


def load_ui_settings(settings_file: Path) -> UiSettings:
    if not settings_file.exists():
        return UiSettings()

    try:
        payload = json.loads(settings_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return UiSettings()

    export_format = str(payload.get("export_format", "txt")).strip().lower()
    if export_format not in {"txt", "mid", "musicxml"}:
        export_format = "txt"

    export_dir = str(payload.get("export_dir", "./outputs")).strip()
    if not export_dir:
        export_dir = "./outputs"

    return UiSettings(export_format=export_format, export_dir=export_dir)


def save_ui_settings(settings_file: Path, settings: UiSettings) -> None:
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")