from __future__ import annotations

from pathlib import Path

from src.config.settings import ModelAdapterSettings
from src.services import model_update_service
from src.services.model_update_service import mark_model_updated
from src.services.offline_health_service import get_offline_health_report


def _build_settings(tmp_path: Path) -> ModelAdapterSettings:
    return ModelAdapterSettings(
        demucs_model_path=tmp_path / "models" / "demucs",
        crepe_model_path=tmp_path / "models" / "crepe",
        basic_pitch_model_path=tmp_path / "models" / "basic_pitch",
    )


def test_offline_health_report_not_ready_when_cache_and_versions_missing(tmp_path: Path) -> None:
    report = get_offline_health_report(_build_settings(tmp_path))

    assert report.ready_for_offline is False
    assert report.missing_models == ("demucs", "crepe", "basic_pitch")
    assert report.pending_update_models == ("demucs", "crepe", "basic_pitch")


def test_offline_health_report_ready_when_cache_and_versions_are_ready(tmp_path: Path, monkeypatch) -> None:
    settings = _build_settings(tmp_path)
    monkeypatch.setattr(model_update_service, "_is_runtime_available", lambda _name: True)
    for model_path in (settings.demucs_model_path, settings.crepe_model_path, settings.basic_pitch_model_path):
        model_path.mkdir(parents=True, exist_ok=True)
        (model_path / "weights.bin").write_bytes(b"x")

    mark_model_updated(settings, "demucs")
    mark_model_updated(settings, "crepe")
    mark_model_updated(settings, "basic_pitch")

    report = get_offline_health_report(settings)

    assert report.ready_for_offline is True
    assert report.missing_models == ()
    assert report.pending_update_models == ()
