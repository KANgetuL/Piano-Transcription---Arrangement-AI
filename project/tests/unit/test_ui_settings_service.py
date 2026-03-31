from __future__ import annotations

from pathlib import Path

from src.services.ui_settings_service import UiSettings, load_ui_settings, save_ui_settings


def test_load_ui_settings_returns_defaults_when_missing(tmp_path: Path) -> None:
    settings = load_ui_settings(tmp_path / "missing.json")

    assert settings.export_format == "txt"
    assert settings.export_dir == "./outputs"
    assert settings.upload_dir == "."
    assert settings.language == "zh_CN"
    assert settings.runtime_mode == "normal"
    assert settings.show_onboarding_tip is True


def test_save_and_load_ui_settings_roundtrip(tmp_path: Path) -> None:
    settings_file = tmp_path / "ui_settings.json"
    save_ui_settings(
        settings_file,
        UiSettings(
            export_format="musicxml",
            export_dir="./custom_outputs",
            upload_dir="./audio",
            language="en_US",
            runtime_mode="strict",
            show_onboarding_tip=False,
        ),
    )

    settings = load_ui_settings(settings_file)

    assert settings.export_format == "musicxml"
    assert settings.export_dir == "./custom_outputs"
    assert settings.upload_dir == "./audio"
    assert settings.language == "en_US"
    assert settings.runtime_mode == "strict"
    assert settings.show_onboarding_tip is False


def test_load_ui_settings_normalizes_invalid_values(tmp_path: Path) -> None:
    settings_file = tmp_path / "ui_settings.json"
    settings_file.write_text(
        '{"export_format":"PDF","export_dir":"","upload_dir":"","language":"fr_FR","runtime_mode":"expert","show_onboarding_tip":"yes"}',
        encoding="utf-8",
    )

    settings = load_ui_settings(settings_file)

    assert settings.export_format == "txt"
    assert settings.export_dir == "./outputs"
    assert settings.upload_dir == "."
    assert settings.language == "zh_CN"
    assert settings.runtime_mode == "normal"
    assert settings.show_onboarding_tip is True