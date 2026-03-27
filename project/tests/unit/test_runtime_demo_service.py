from __future__ import annotations

from src.services import runtime_demo_service
from src.services.runtime_probe_service import RuntimeProbeResult


def test_run_runtime_demo_success(monkeypatch) -> None:
    monkeypatch.setattr(
        runtime_demo_service,
        "probe_model_runtime",
        lambda: RuntimeProbeResult(
            demucs_available=True,
            crepe_available=True,
            basic_pitch_available=True,
        ),
    )
    monkeypatch.setattr(
        runtime_demo_service.SeparationAdapter,
        "runtime_check",
        lambda _self: (True, "ok-separation"),
    )
    monkeypatch.setattr(
        runtime_demo_service.PitchAdapter,
        "runtime_check",
        lambda _self: (True, "ok-pitch"),
    )
    monkeypatch.setattr(
        runtime_demo_service.HarmonyAdapter,
        "runtime_check",
        lambda _self: (True, "ok-harmony"),
    )

    report = runtime_demo_service.run_runtime_demo()

    assert report.all_ok is True
    assert report.python_runtime_missing_modules == ()
    assert tuple(item.ok for item in report.stage_status) == (True, True, True)


def test_run_runtime_demo_partial_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        runtime_demo_service,
        "probe_model_runtime",
        lambda: RuntimeProbeResult(
            demucs_available=True,
            crepe_available=False,
            basic_pitch_available=True,
        ),
    )
    monkeypatch.setattr(
        runtime_demo_service.SeparationAdapter,
        "runtime_check",
        lambda _self: (True, "ok-separation"),
    )
    monkeypatch.setattr(
        runtime_demo_service.PitchAdapter,
        "runtime_check",
        lambda _self: (False, "missing-crepe"),
    )
    monkeypatch.setattr(
        runtime_demo_service.HarmonyAdapter,
        "runtime_check",
        lambda _self: (True, "ok-harmony"),
    )

    report = runtime_demo_service.run_runtime_demo()

    assert report.all_ok is False
    assert report.python_runtime_ok is False
    assert report.python_runtime_missing_modules == ("crepe",)
    assert report.stage_status[1].ok is False
