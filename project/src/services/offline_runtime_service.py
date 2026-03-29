from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.config.settings import ModelAdapterSettings


@dataclass(frozen=True, slots=True)
class OfflineModelCacheItem:
    name: str
    path: Path
    cached: bool


@dataclass(frozen=True, slots=True)
class OfflineRuntimeStatus:
    items: tuple[OfflineModelCacheItem, ...]

    @property
    def all_cached(self) -> bool:
        return all(item.cached for item in self.items)

    @property
    def missing_models(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.items if not item.cached)


def inspect_offline_runtime(settings: ModelAdapterSettings) -> OfflineRuntimeStatus:
    def _cached(path: Path) -> bool:
        if not path.exists() or not path.is_dir():
            return False
        try:
            next(path.iterdir())
            return True
        except StopIteration:
            return False

    items = (
        OfflineModelCacheItem(name="demucs", path=settings.demucs_model_path, cached=_cached(settings.demucs_model_path)),
        OfflineModelCacheItem(name="crepe", path=settings.crepe_model_path, cached=_cached(settings.crepe_model_path)),
        OfflineModelCacheItem(
            name="basic_pitch",
            path=settings.basic_pitch_model_path,
            cached=_cached(settings.basic_pitch_model_path),
        ),
    )
    return OfflineRuntimeStatus(items=items)


def ensure_offline_cache_dirs(settings: ModelAdapterSettings) -> OfflineRuntimeStatus:
    for path in (settings.demucs_model_path, settings.crepe_model_path, settings.basic_pitch_model_path):
        path.mkdir(parents=True, exist_ok=True)
    return inspect_offline_runtime(settings)