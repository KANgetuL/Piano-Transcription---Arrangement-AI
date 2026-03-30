from __future__ import annotations

from src.services.i18n_service import mode_description_localized, normalize_language, ui_text


def test_normalize_language_fallbacks_to_zh_cn() -> None:
    assert normalize_language("fr_FR") == "zh_CN"


def test_ui_text_uses_selected_language() -> None:
    assert ui_text("en_US", "start") == "Start"
    assert ui_text("zh_CN", "start") == "开始处理"
    assert ui_text("zh_CN", "export_all") == "批量导出"
    assert ui_text("en_US", "export_all") == "Batch Export"
    assert ui_text("zh_CN", "batch_upload_no_valid") == "未选择可用的音频文件。"
    assert ui_text("en_US", "runtime_mode") == "Runtime Mode"
    assert ui_text("zh_CN", "offline_check") == "离线检查"
    assert ui_text("zh_CN", "offline_health_check") == "离线自检"
    assert ui_text("en_US", "offline_health_check") == "Offline Health"
    assert ui_text("en_US", "update_check") == "Check Updates"


def test_mode_description_localized_switches_language() -> None:
    zh_desc = mode_description_localized("normal", "zh_CN")
    en_desc = mode_description_localized("normal", "en_US")

    assert "普通钢琴谱" in zh_desc
    assert "Standard piano score" in en_desc