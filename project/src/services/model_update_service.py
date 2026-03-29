from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.config.settings import ModelAdapterSettings

TARGET_MODEL_VERSIONS: dict[str, str] = {
    "demucs": "v1",
    "crepe": "v1",
    "basic_pitch": "v1",
}


@dataclass(frozen=True, slots=True)
class ModelVersionItem:
    name: str
    path: Path
    installed_version: str | None
    target_version: str
    needs_update: bool


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


def check_model_updates(settings: ModelAdapterSettings) -> ModelUpdateReport:
    items: list[ModelVersionItem] = []
    for name, path in _model_paths(settings):
        target = TARGET_MODEL_VERSIONS[name]
        installed = _read_version(path)
        needs_update = installed != target
        items.append(
            ModelVersionItem(
                name=name,
                path=path,
                installed_version=installed,
                target_version=target,
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