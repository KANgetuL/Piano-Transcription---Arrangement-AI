from __future__ import annotations

from src.services.i18n_service import mode_description_localized, normalize_language, progress_stage_localized, ui_text


def test_normalize_language_fallbacks_to_zh_cn() -> None:
    assert normalize_language("fr_FR") == "zh_CN"


def test_ui_text_uses_selected_language() -> None:
    assert ui_text("en_US", "start") == "Start"
    assert ui_text("zh_CN", "start") == "开始处理"
    assert ui_text("zh_CN", "export_all") == "批量导出"
    assert ui_text("en_US", "export_all") == "Batch Export"
    assert ui_text("zh_CN", "batch_upload_no_valid") == "未选择可用的音频文件。"
    assert "maximum" in ui_text("en_US", "batch_upload_limit_message")
    assert ui_text("zh_CN", "batch_upload_summary_title") == "批量上传结果"
    assert "Valid files" in ui_text("en_US", "batch_upload_summary_message")
    assert ui_text("en_US", "runtime_mode") == "Runtime Mode"
    assert ui_text("zh_CN", "offline_check") == "离线检查"
    assert ui_text("zh_CN", "offline_health_check") == "离线自检"
    assert ui_text("en_US", "offline_health_check") == "Offline Health"
    assert ui_text("en_US", "update_check") == "Check Updates"
    assert "悬停" in ui_text("zh_CN", "operation_hint_default")
    assert "Hover" in ui_text("en_US", "operation_hint_default")
    assert "batch export" in ui_text("en_US", "hint_export_all").lower()
    assert ui_text("zh_CN", "open_export_dir_title") == "打开导出目录"
    assert "Open export directory" in ui_text("en_US", "open_export_dir_prompt")
    assert ui_text("zh_CN", "onboarding_title") == "欢迎使用"
    assert "Suggested first-run flow" in ui_text("en_US", "onboarding_message")
    assert "预计剩余" in ui_text("zh_CN", "progress_status_with_eta")
    assert "ETA" in ui_text("en_US", "progress_status_with_eta")
    assert "缺失缓存" in ui_text("zh_CN", "offline_health_missing_cache")
    assert "Pending updates" in ui_text("en_US", "offline_health_pending_updates")
    assert "预览已截断" in ui_text("zh_CN", "preview_truncated_suffix")
    assert "preview truncated" in ui_text("en_US", "preview_truncated_suffix")
    assert "联网安装" in ui_text("zh_CN", "update_install_confirm_message")
    assert "Install/update online" in ui_text("en_US", "update_install_confirm_message")
    assert "临时禁用" in ui_text("zh_CN", "update_actions_disabled_message")
    assert "temporarily disabled" in ui_text("en_US", "update_actions_disabled_message")
    assert "成功" in ui_text("zh_CN", "update_install_result_message")
    assert "succeeded" in ui_text("en_US", "update_install_result_message")


def test_mode_description_localized_switches_language() -> None:
    zh_desc = mode_description_localized("normal", "zh_CN")
    en_desc = mode_description_localized("normal", "en_US")

    assert "普通钢琴谱" in zh_desc
    assert "Standard piano score" in en_desc


def test_progress_stage_localized_supports_stage_keys_and_legacy_text() -> None:
    assert progress_stage_localized("progress_done", "zh_CN") == "处理完成"
    assert progress_stage_localized("progress_done", "en_US") == "Completed"
    assert progress_stage_localized("处理完成", "en_US") == "Completed"
    assert progress_stage_localized("unknown-stage", "en_US") == "unknown-stage"