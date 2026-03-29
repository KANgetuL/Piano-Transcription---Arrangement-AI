from __future__ import annotations

from pathlib import Path

from src.services.mode_preference_service import load_last_mode, mode_description, save_last_mode


def test_mode_description_for_pop() -> None:
    assert "流行风格" in mode_description("pop")


def test_load_last_mode_returns_default_on_missing_file(tmp_path: Path) -> None:
    pref = tmp_path / "pref.json"

    value = load_last_mode(pref, default_mode="electronic")

    assert value == "electronic"


def test_save_and_load_last_mode(tmp_path: Path) -> None:
    pref = tmp_path / "pref.json"

    save_last_mode(pref, "classical")
    value = load_last_mode(pref)

    assert value == "classical"


def test_load_last_mode_fallback_on_invalid_json(tmp_path: Path) -> None:
    pref = tmp_path / "pref.json"
    pref.write_text("{invalid", encoding="utf-8")

    value = load_last_mode(pref, default_mode="normal")

    assert value == "normal"
