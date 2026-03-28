from __future__ import annotations

import json
from pathlib import Path

from src.models.entities import TranscriptionMode

MODE_DESCRIPTIONS: dict[TranscriptionMode, str] = {
    "normal": "普通钢琴谱：主旋律 + 基础和弦，适合日常演奏。",
    "pop": "流行风格：右手旋律、左手流行分解和弦。",
    "electronic": "电子风格：强化节奏量化与低音循环感。",
    "classical": "古典风格：保留多声部与更细腻织体。",
    "black": "黑乐谱：高密度音符与强化视觉效果。",
}


def mode_description(mode: TranscriptionMode) -> str:
    """Return user-facing description text for a transcription mode."""

    return MODE_DESCRIPTIONS[mode]


def load_last_mode(preference_file: Path, default_mode: TranscriptionMode = "normal") -> TranscriptionMode:
    """Load last selected mode from local preference file."""

    if not preference_file.exists():
        return default_mode

    try:
        data = json.loads(preference_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_mode

    value = data.get("last_mode")
    if value in MODE_DESCRIPTIONS:
        return value
    return default_mode


def save_last_mode(preference_file: Path, mode: TranscriptionMode) -> None:
    """Persist selected mode into local preference file."""

    preference_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {"last_mode": mode}
    preference_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
