from __future__ import annotations

from typing import Literal

from src.models.entities import TranscriptionMode

LanguageCode = Literal["zh_CN", "en_US"]

_SUPPORTED_LANGUAGES: tuple[LanguageCode, ...] = ("zh_CN", "en_US")

_TEXTS: dict[LanguageCode, dict[str, str]] = {
    "zh_CN": {
        "audio_file": "音频文件",
        "choose_file": "选择文件",
        "upload_list": "上传文件列表（最近 5 个）",
        "refresh": "刷新",
        "rename": "重命名",
        "delete": "删除",
        "upload_hint_default": "请选择文件后可查看并管理最近上传记录",
        "mode": "模式",
        "start": "开始处理",
        "cancel": "取消任务",
        "export_format": "导出格式",
        "export_dir": "导出目录",
        "choose": "选择",
        "export_current": "导出当前乐谱",
        "clear_cache": "清理缓存",
        "language": "语言",
        "runtime_mode": "运行模式",
        "preview": "乐谱预览（文本）",
        "preview_placeholder": "处理完成后将显示导出文本内容。",
        "ready": "就绪",
        "cache_status": "缓存占用: {count} 文件 / {size_kb:.1f} KB",
        "prompt": "提示",
        "warning": "警告",
        "error": "错误",
        "complete": "完成",
        "cache_management": "缓存管理",
        "choose_audio_file": "选择音频文件",
        "select_file_before_refresh": "请先选择音频文件后再刷新上传列表。",
        "select_upload_first": "请先在列表中选择一个文件。",
        "rename_prompt": "输入新文件名（可不带后缀）",
        "confirm_delete": "确认删除",
        "confirm_delete_message": "确定删除文件: {filename} ?",
        "task_running_tip": "已有任务在运行，请稍候。",
        "select_file_before_start": "请先选择音频文件。",
        "processing": "处理中...",
        "preview_loading": "处理中，完成后将加载导出预览。",
        "task_cancelled": "任务已取消",
        "task_failed": "处理失败",
        "completed": "完成: {output_path}",
        "complete_message": "导出文件: {output_path}",
        "preview_load_failed": "预览加载失败: {error}",
        "cancel_not_supported": "任务已开始执行，当前版本暂不支持中途取消。",
        "no_score_to_export": "当前没有可导出的乐谱。",
        "export_success": "导出成功",
        "export_success_message": "已导出: {output_path}",
        "cache_cleared": "已清理缓存文件: {removed} 个",
        "upload_loaded_hint": "当前目录: {upload_dir} | 已加载 {count} 条",
        "runtime_mode_normal": "normal",
        "runtime_mode_strict": "strict",
    },
    "en_US": {
        "audio_file": "Audio File",
        "choose_file": "Choose File",
        "upload_list": "Recent Uploads (Last 5)",
        "refresh": "Refresh",
        "rename": "Rename",
        "delete": "Delete",
        "upload_hint_default": "Choose a file to view and manage recent uploads",
        "mode": "Mode",
        "start": "Start",
        "cancel": "Cancel Task",
        "export_format": "Export Format",
        "export_dir": "Export Directory",
        "choose": "Choose",
        "export_current": "Export Current Score",
        "clear_cache": "Clear Cache",
        "language": "Language",
        "runtime_mode": "Runtime Mode",
        "preview": "Score Preview (Text)",
        "preview_placeholder": "The exported text preview will appear after processing.",
        "ready": "Ready",
        "cache_status": "Cache Usage: {count} files / {size_kb:.1f} KB",
        "prompt": "Notice",
        "warning": "Warning",
        "error": "Error",
        "complete": "Done",
        "cache_management": "Cache Management",
        "choose_audio_file": "Choose Audio File",
        "select_file_before_refresh": "Please choose an audio file before refreshing uploads.",
        "select_upload_first": "Please select a file from the list first.",
        "rename_prompt": "Enter a new file name (extension optional)",
        "confirm_delete": "Confirm Delete",
        "confirm_delete_message": "Delete file: {filename}?",
        "task_running_tip": "A task is already running. Please wait.",
        "select_file_before_start": "Please choose an audio file first.",
        "processing": "Processing...",
        "preview_loading": "Processing. Preview will be loaded when done.",
        "task_cancelled": "Task cancelled",
        "task_failed": "Processing failed",
        "completed": "Completed: {output_path}",
        "complete_message": "Exported file: {output_path}",
        "preview_load_failed": "Failed to load preview: {error}",
        "cancel_not_supported": "Task has started; this version cannot cancel mid-run.",
        "no_score_to_export": "No score is available for export.",
        "export_success": "Export Success",
        "export_success_message": "Exported to: {output_path}",
        "cache_cleared": "Cleared cache files: {removed}",
        "upload_loaded_hint": "Current folder: {upload_dir} | Loaded: {count}",
        "runtime_mode_normal": "normal",
        "runtime_mode_strict": "strict",
    },
}

_MODE_DESCRIPTIONS: dict[LanguageCode, dict[TranscriptionMode, str]] = {
    "zh_CN": {
        "normal": "普通钢琴谱：主旋律 + 基础和弦，适合日常演奏。",
        "pop": "流行风格：右手旋律、左手流行分解和弦。",
        "electronic": "电子风格：强化节奏量化与低音循环感。",
        "classical": "古典风格：保留多声部与更细腻织体。",
        "black": "黑乐谱：高密度音符与强化视觉效果。",
    },
    "en_US": {
        "normal": "Standard piano score: melody + core chords for daily practice.",
        "pop": "Pop style: right-hand melody with left-hand pop arpeggios.",
        "electronic": "Electronic style: stronger quantization and bass-loop feel.",
        "classical": "Classical style: preserves polyphony with richer texture.",
        "black": "Black score: high note density with strong visual impact.",
    },
}


def normalize_language(value: str) -> LanguageCode:
    cleaned = value.strip()
    if cleaned in _SUPPORTED_LANGUAGES:
        return cleaned  # type: ignore[return-value]
    return "zh_CN"


def language_options() -> tuple[LanguageCode, ...]:
    return _SUPPORTED_LANGUAGES


def ui_text(language: str, key: str) -> str:
    lang = normalize_language(language)
    return _TEXTS[lang].get(key, key)


def mode_description_localized(mode: TranscriptionMode, language: str) -> str:
    lang = normalize_language(language)
    return _MODE_DESCRIPTIONS[lang][mode]