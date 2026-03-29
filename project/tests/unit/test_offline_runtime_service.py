from __future__ import annotations

from pathlib import Path

from src.config.settings import ModelAdapterSettings
from src.services.offline_runtime_service import ensure_offline_cache_dirs, inspect_offline_runtime


def _build_settings(tmp_path: Path) -> ModelAdapterSettings:
    return ModelAdapterSettings(
        demucs_model_path=tmp_path / "models" / "demucs",
        crepe_model_path=tmp_path / "models" / "crepe",
        basic_pitch_model_path=tmp_path / "models" / "basic_pitch",
    )


def test_inspect_offline_runtime_returns_missing_for_absent_cache(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)

    status = inspect_offline_runtime(settings)

    assert status.all_cached is False
    assert status.missing_models == ("demucs", "crepe", "basic_pitch")


def test_ensure_offline_cache_dirs_creates_expected_paths(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)

    status = ensure_offline_cache_dirs(settings)

    assert status.all_cached is False
    assert status.missing_models == ("demucs", "crepe", "basic_pitch")
    assert settings.demucs_model_path.exists()
    assert settings.crepe_model_path.exists()
    assert settings.basic_pitch_model_path.exists()


def test_inspect_offline_runtime_mixed_state(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)
    settings.demucs_model_path.mkdir(parents=True)
    (settings.demucs_model_path / "weights.bin").write_bytes(b"x")

    status = inspect_offline_runtime(settings)

    assert status.all_cached is False
    assert status.missing_models == ("crepe", "basic_pitch")