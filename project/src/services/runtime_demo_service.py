from __future__ import annotations

from dataclasses import dataclass

from src.config.settings import get_settings
from src.services.model_adapters import HarmonyAdapter, PitchAdapter, SeparationAdapter
from src.services.runtime_probe_service import probe_model_runtime


@dataclass(frozen=True, slots=True)
class StageRuntimeStatus:
    stage: str
    ok: bool
    detail: str


@dataclass(frozen=True, slots=True)
class RuntimeDemoReport:
    python_runtime_ok: bool
    python_runtime_missing_modules: tuple[str, ...]
    stage_status: tuple[StageRuntimeStatus, ...]

    @property
    def all_ok(self) -> bool:
        return self.python_runtime_ok and all(item.ok for item in self.stage_status)


def run_runtime_demo() -> RuntimeDemoReport:
    """Produce a lightweight, non-inference runtime demo report for model stack callability."""

    settings = get_settings().model
    runtime_probe = probe_model_runtime()

    separation_ok, separation_detail = SeparationAdapter.from_settings(settings).runtime_check()
    pitch_ok, pitch_detail = PitchAdapter.from_settings(settings).runtime_check()
    harmony_ok, harmony_detail = HarmonyAdapter.from_settings(settings).runtime_check()

    stage_status = (
        StageRuntimeStatus(stage="separation", ok=separation_ok, detail=separation_detail),
        StageRuntimeStatus(stage="pitch", ok=pitch_ok, detail=pitch_detail),
        StageRuntimeStatus(stage="harmony", ok=harmony_ok, detail=harmony_detail),
    )

    return RuntimeDemoReport(
        python_runtime_ok=runtime_probe.all_available,
        python_runtime_missing_modules=runtime_probe.missing_modules,
        stage_status=stage_status,
    )
