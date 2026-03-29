from __future__ import annotations

from dataclasses import dataclass

from src.config.settings import ModelAdapterSettings
from src.services.model_update_service import ModelUpdateReport, check_model_updates
from src.services.offline_runtime_service import OfflineRuntimeStatus, inspect_offline_runtime


@dataclass(frozen=True, slots=True)
class OfflineHealthReport:
    runtime_status: OfflineRuntimeStatus
    update_report: ModelUpdateReport

    @property
    def ready_for_offline(self) -> bool:
        return self.runtime_status.all_cached and not self.update_report.has_updates

    @property
    def missing_models(self) -> tuple[str, ...]:
        return self.runtime_status.missing_models

    @property
    def pending_update_models(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.update_report.items if item.needs_update)


def get_offline_health_report(settings: ModelAdapterSettings) -> OfflineHealthReport:
    runtime_status = inspect_offline_runtime(settings)
    update_report = check_model_updates(settings)
    return OfflineHealthReport(runtime_status=runtime_status, update_report=update_report)
