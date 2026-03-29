from __future__ import annotations

from pathlib import Path

import pytest

from src.config.settings import ModelAdapterSettings
from src.services.model_update_service import check_model_updates, mark_model_updated


def _build_settings(tmp_path: Path) -> ModelAdapterSettings:
    return ModelAdapterSettings(
        demucs_model_path=tmp_path / "models" / "demucs",
        crepe_model_path=tmp_path / "models" / "crepe",
        basic_pitch_model_path=tmp_path / "models" / "basic_pitch",
    )


def test_check_model_updates_reports_all_missing_when_no_versions(tmp_path: Path) -> None:
    report = check_model_updates(_build_settings(tmp_path))

    assert report.has_updates is True
    assert report.update_count == 3


def test_mark_model_updated_updates_single_model_state(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)

    report = mark_model_updated(settings, "demucs")

    items = {item.name: item for item in report.items}
    assert items["demucs"].needs_update is False
    assert items["crepe"].needs_update is True
    assert items["basic_pitch"].needs_update is True


def test_mark_model_updated_rejects_unknown_model(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)

    with pytest.raises(ValueError):
        mark_model_updated(settings, "unknown")