from __future__ import annotations

from pathlib import Path

import pytest

from src.config.settings import ModelAdapterSettings
from src.services import model_update_service
from src.services.model_update_service import check_model_updates, install_or_update_models_online, mark_model_updated


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


def test_check_model_updates_detects_missing_runtime_even_with_version_file(tmp_path: Path, monkeypatch) -> None:
    settings = _build_settings(tmp_path)
    for model_name in ("demucs", "crepe", "basic_pitch"):
        mark_model_updated(settings, model_name)

    monkeypatch.setattr(
        model_update_service,
        "_is_runtime_available",
        lambda model_name: model_name != "crepe",
    )

    report = check_model_updates(settings)
    items = {item.name: item for item in report.items}
    assert items["demucs"].needs_update is False
    assert items["crepe"].needs_update is True
    assert items["crepe"].runtime_available is False


def test_install_or_update_models_online_writes_version_on_success(tmp_path: Path, monkeypatch) -> None:
    settings = _build_settings(tmp_path)
    called_commands: list[tuple[str, ...]] = []

    class _SuccessResult:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(command: tuple[str, ...], **_kwargs: object) -> _SuccessResult:
        called_commands.append(command)
        return _SuccessResult()

    monkeypatch.setattr(model_update_service.subprocess, "run", _fake_run)

    install_report = install_or_update_models_online(settings, ("demucs",))
    assert install_report.success_count == 1
    assert install_report.failed_count == 0
    assert called_commands
    assert "pip" in called_commands[0]
    assert (settings.demucs_model_path / ".version").read_text(encoding="utf-8") == "v1"


def test_install_or_update_models_online_reports_failure(tmp_path: Path, monkeypatch) -> None:
    settings = _build_settings(tmp_path)

    class _FailResult:
        returncode = 1
        stdout = ""
        stderr = "network timeout"

    monkeypatch.setattr(model_update_service.subprocess, "run", lambda *_args, **_kwargs: _FailResult())

    install_report = install_or_update_models_online(settings, ("crepe",))
    assert install_report.success_count == 0
    assert install_report.failed_count == 1
    assert "network timeout" in install_report.items[0].detail