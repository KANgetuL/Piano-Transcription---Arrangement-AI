from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import subprocess
import sys

from src.config.settings import ModelAdapterSettings

TARGET_MODEL_VERSIONS: dict[str, str] = {
    "demucs": "v1",
    "crepe": "v1",
    "basic_pitch": "v1",
}

MODEL_INSTALL_SPECS: dict[str, str] = {
    "demucs": "demucs>=4.0.0",
    "crepe": "crepe",
    "basic_pitch": "basic-pitch",
}

_RUNTIME_MODULES: dict[str, str] = {
    "demucs": "demucs",
    "crepe": "crepe",
    "basic_pitch": "basic_pitch",
}


@dataclass(frozen=True, slots=True)
class ModelVersionItem:
    name: str
    path: Path
    installed_version: str | None
    target_version: str
    runtime_available: bool
    needs_update: bool


@dataclass(frozen=True, slots=True)
class ModelInstallItem:
    name: str
    command: tuple[str, ...]
    success: bool
    detail: str


@dataclass(frozen=True, slots=True)
class ModelInstallReport:
    items: tuple[ModelInstallItem, ...]

    @property
    def success_count(self) -> int:
        return sum(1 for item in self.items if item.success)

    @property
    def failed_count(self) -> int:
        return sum(1 for item in self.items if not item.success)


@dataclass(frozen=True, slots=True)
class ModelUpdateReport:
    items: tuple[ModelVersionItem, ...]

    @property
    def has_updates(self) -> bool:
        return any(item.needs_update for item in self.items)

    @property
    def update_count(self) -> int:
        return sum(1 for item in self.items if item.needs_update)


def _version_file(model_dir: Path) -> Path:
    return model_dir / ".version"


def _read_version(model_dir: Path) -> str | None:
    version_file = _version_file(model_dir)
    if not version_file.exists():
        return None
    value = version_file.read_text(encoding="utf-8").strip()
    return value or None


def _write_version(model_dir: Path, version: str) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    _version_file(model_dir).write_text(version, encoding="utf-8")


def _model_paths(settings: ModelAdapterSettings) -> tuple[tuple[str, Path], ...]:
    return (
        ("demucs", settings.demucs_model_path),
        ("crepe", settings.crepe_model_path),
        ("basic_pitch", settings.basic_pitch_model_path),
    )


def _is_runtime_available(model_name: str) -> bool:
    module_name = _RUNTIME_MODULES[model_name]
    return importlib.util.find_spec(module_name) is not None


def check_model_updates(settings: ModelAdapterSettings) -> ModelUpdateReport:
    items: list[ModelVersionItem] = []
    for name, path in _model_paths(settings):
        target = TARGET_MODEL_VERSIONS[name]
        installed = _read_version(path)
        runtime_available = _is_runtime_available(name)
        needs_update = installed != target or not runtime_available
        items.append(
            ModelVersionItem(
                name=name,
                path=path,
                installed_version=installed,
                target_version=target,
                runtime_available=runtime_available,
                needs_update=needs_update,
            )
        )
    return ModelUpdateReport(items=tuple(items))


def mark_model_updated(settings: ModelAdapterSettings, model_name: str) -> ModelUpdateReport:
    model_name = model_name.strip().lower()
    target = TARGET_MODEL_VERSIONS.get(model_name)
    if target is None:
        raise ValueError(f"Unsupported model name: {model_name}")

    for name, path in _model_paths(settings):
        if name == model_name:
            _write_version(path, target)
            break

    return check_model_updates(settings)


def install_or_update_models_online(
    settings: ModelAdapterSettings,
    model_names: tuple[str, ...] | None = None,
) -> ModelInstallReport:
    names = model_names or tuple(name for name, _ in _model_paths(settings))
    items: list[ModelInstallItem] = []

    for name in names:
        normalized = name.strip().lower()
        target_version = TARGET_MODEL_VERSIONS.get(normalized)
        spec = MODEL_INSTALL_SPECS.get(normalized)
        if target_version is None or spec is None:
            raise ValueError(f"Unsupported model name: {name}")

        command = (sys.executable, "-m", "pip", "install", "--upgrade", spec)
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            path = dict(_model_paths(settings))[normalized]
            _write_version(path, target_version)
            detail = (result.stdout or "installed").strip().splitlines()[-1]
            items.append(ModelInstallItem(name=normalized, command=command, success=True, detail=detail))
            continue

        error_text = (result.stderr or result.stdout or "install failed").strip()
        items.append(
            ModelInstallItem(
                name=normalized,
                command=command,
                success=False,
                detail=error_text,
            )
        )

    return ModelInstallReport(items=tuple(items))