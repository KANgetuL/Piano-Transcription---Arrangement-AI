from __future__ import annotations

from dataclasses import dataclass
import importlib.util


@dataclass(frozen=True, slots=True)
class RuntimeProbeResult:
    """Runtime availability info for optional model SDK packages."""

    demucs_available: bool
    crepe_available: bool
    basic_pitch_available: bool

    @property
    def all_available(self) -> bool:
        return self.demucs_available and self.crepe_available and self.basic_pitch_available

    @property
    def missing_modules(self) -> tuple[str, ...]:
        missing: list[str] = []
        if not self.demucs_available:
            missing.append("demucs")
        if not self.crepe_available:
            missing.append("crepe")
        if not self.basic_pitch_available:
            missing.append("basic_pitch")
        return tuple(missing)


def _has_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def probe_model_runtime() -> RuntimeProbeResult:
    """Probe optional model SDKs without importing heavy packages."""

    return RuntimeProbeResult(
        demucs_available=_has_module("demucs"),
        crepe_available=_has_module("crepe"),
        basic_pitch_available=_has_module("basic_pitch"),
    )
