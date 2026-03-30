from __future__ import annotations

import os
import tkinter as tk
from concurrent.futures import CancelledError
from concurrent.futures import Future
from pathlib import Path
from queue import Empty, SimpleQueue
from tkinter import filedialog, messagebox, simpledialog, ttk

from src.app.upload_workflow import collect_batch_upload_files, delete_uploaded_file, list_recent_uploads, rename_uploaded_file
from src.models.entities import ScoreDocument
from src.config.settings import get_settings
from src.services.cache_management_service import clear_cache, get_cache_status
from src.services.i18n_service import language_options, mode_description_localized, ui_text
from src.services.model_update_service import check_model_updates, mark_model_updated
from src.services.mode_preference_service import load_last_mode, save_last_mode
from src.services.offline_health_service import get_offline_health_report
from src.services.offline_runtime_service import OfflineRuntimeStatus, ensure_offline_cache_dirs, inspect_offline_runtime
from src.models.entities import AudioFileInfo
from src.models.entities import TranscriptionMode
from src.services.export_service import export_score, export_scores
from src.services.score_preview_service import load_score_preview
from src.services.task_queue_service import TaskQueueService
from src.services.ui_settings_service import UiSettings, load_ui_settings, save_ui_settings
from src.utils.logging_utils import configure_logging


class DesktopApp(tk.Tk):
    """Minimal desktop UI shell for local transcription workflow."""

    def __init__(self) -> None:
        super().__init__()
        self.title("PianoTrans AI - Minimal UI")
        self.geometry("760x460")
        self.minsize(640, 400)

        self.queue_service = TaskQueueService(worker_count=1)
        self.current_future: Future | None = None
        self.selected_path = tk.StringVar(value="")
        self.preference_file = Path("./cache/ui_preferences.json")
        self.ui_settings_file = Path("./cache/ui_settings.json")
        self.transcription_cache_dir = Path("./cache/transcription_cache")
        self.model_settings = get_settings().model
        initial_mode = load_last_mode(self.preference_file)
        ui_settings = load_ui_settings(self.ui_settings_file)
        self.language_var = tk.StringVar(value=ui_settings.language)
        self.mode_var = tk.StringVar(value=initial_mode)
        self.status_var = tk.StringVar(value=ui_text(self.language_var.get(), "ready"))
        self.progress_var = tk.IntVar(value=0)
        self.mode_desc_var = tk.StringVar(value=mode_description_localized(initial_mode, self.language_var.get()))
        self.upload_items: list[AudioFileInfo] = []
        self.progress_updates: SimpleQueue[tuple[int, str, float | None]] = SimpleQueue()
        self.preview_text: tk.Text | None = None
        self.export_format_var = tk.StringVar(value=ui_settings.export_format)
        self.export_dir_var = tk.StringVar(value=ui_settings.export_dir)
        self.upload_dir_var = tk.StringVar(value=ui_settings.upload_dir)
        self.runtime_mode_var = tk.StringVar(value=ui_settings.runtime_mode)
        self.cache_status_var = tk.StringVar(value="")
        self.offline_status_var = tk.StringVar(value="")
        self.offline_health_var = tk.StringVar(value="")
        self.update_status_var = tk.StringVar(value="")
        self.last_score: ScoreDocument | None = None
        self.processed_scores: list[ScoreDocument] = []

        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)

        self.audio_label = ttk.Label(root, text="")
        self.audio_label.grid(row=0, column=0, sticky=tk.W)
        entry = ttk.Entry(root, textvariable=self.selected_path, width=70)
        entry.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(4, 10))

        self.pick_file_btn = ttk.Button(root, text="", command=self._pick_file)
        self.pick_file_btn.grid(row=2, column=0, sticky=tk.W)

        self.upload_frame = ttk.LabelFrame(root, text="", padding=8)
        self.upload_frame.grid(row=3, column=0, columnspan=3, sticky=tk.NSEW, pady=(14, 0))

        self.upload_tree = ttk.Treeview(
            self.upload_frame,
            columns=("name", "size", "duration", "ext"),
            show="headings",
            height=5,
        )
        self.upload_tree.column("name", width=320, anchor=tk.W)
        self.upload_tree.column("size", width=90, anchor=tk.E)
        self.upload_tree.column("duration", width=90, anchor=tk.E)
        self.upload_tree.column("ext", width=70, anchor=tk.CENTER)
        self.upload_tree.grid(row=0, column=0, columnspan=4, sticky=tk.NSEW)
        self.upload_tree.bind("<<TreeviewSelect>>", self._on_upload_select)

        self.refresh_upload_btn = ttk.Button(self.upload_frame, text="", command=self._refresh_uploads)
        self.refresh_upload_btn.grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        self.rename_upload_btn = ttk.Button(self.upload_frame, text="", command=self._rename_selected_upload)
        self.rename_upload_btn.grid(
            row=1, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )
        self.delete_upload_btn = ttk.Button(self.upload_frame, text="", command=self._delete_selected_upload)
        self.delete_upload_btn.grid(
            row=1, column=2, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )
        self.upload_frame.columnconfigure(0, weight=1)

        self.upload_hint = tk.StringVar(value="")
        self.upload_hint_label = ttk.Label(self.upload_frame, textvariable=self.upload_hint)
        self.upload_hint_label.grid(row=1, column=3, sticky=tk.E, padx=(8, 0), pady=(8, 0))

        self.mode_label = ttk.Label(root, text="")
        self.mode_label.grid(row=4, column=0, sticky=tk.W, pady=(16, 0))
        mode_box = ttk.Combobox(
            root,
            textvariable=self.mode_var,
            values=["normal", "pop", "electronic", "classical", "black"],
            state="readonly",
            width=22,
        )
        mode_box.grid(row=5, column=0, sticky=tk.W, pady=(4, 0))
        mode_box.bind("<<ComboboxSelected>>", self._on_mode_changed)

        ttk.Label(root, textvariable=self.mode_desc_var, foreground="#555555", wraplength=520).grid(
            row=5, column=2, sticky=tk.W, pady=(4, 0)
        )

        self.start_btn = ttk.Button(root, text="开始处理", command=self._start_task)
        self.start_btn.grid(row=5, column=1, sticky=tk.W, padx=(12, 0), pady=(4, 0))
        self.cancel_btn = ttk.Button(root, text="取消任务", command=self._cancel_task, state=tk.DISABLED)
        self.cancel_btn.grid(row=5, column=2, sticky=tk.E, pady=(4, 0))

        export_frame = ttk.Frame(root)
        export_frame.grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=(6, 0))
        self.export_format_label = ttk.Label(export_frame, text="")
        self.export_format_label.grid(row=0, column=0, sticky=tk.W)
        export_format_box = ttk.Combobox(
            export_frame,
            textvariable=self.export_format_var,
            values=["txt", "mid", "musicxml"],
            state="readonly",
            width=12,
        )
        export_format_box.grid(row=0, column=1, sticky=tk.W, padx=(8, 0))
        export_format_box.bind("<<ComboboxSelected>>", self._on_export_setting_changed)

        self.export_dir_label = ttk.Label(export_frame, text="")
        self.export_dir_label.grid(row=0, column=2, sticky=tk.W, padx=(12, 0))
        ttk.Entry(export_frame, textvariable=self.export_dir_var, width=26).grid(row=0, column=3, sticky=tk.W, padx=(8, 0))
        self.pick_export_dir_btn = ttk.Button(export_frame, text="", command=self._pick_export_dir)
        self.pick_export_dir_btn.grid(row=0, column=4, sticky=tk.W, padx=(8, 0))
        self.export_btn = ttk.Button(export_frame, text="", command=self._export_current_score, state=tk.DISABLED)
        self.export_btn.grid(row=0, column=5, sticky=tk.W, padx=(12, 0))
        self.batch_export_btn = ttk.Button(export_frame, text="", command=self._export_all_scores, state=tk.DISABLED)
        self.batch_export_btn.grid(row=0, column=6, sticky=tk.W, padx=(8, 0))

        self.clear_cache_btn = ttk.Button(export_frame, text="", command=self._clear_cache)
        self.clear_cache_btn.grid(row=0, column=7, sticky=tk.W, padx=(12, 0))
        ttk.Label(export_frame, textvariable=self.cache_status_var).grid(row=0, column=8, sticky=tk.W, padx=(8, 0))

        self.language_label = ttk.Label(export_frame, text="")
        self.language_label.grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        self.language_box = ttk.Combobox(
            export_frame,
            textvariable=self.language_var,
            values=list(language_options()),
            state="readonly",
            width=12,
        )
        self.language_box.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=(6, 0))
        self.language_box.bind("<<ComboboxSelected>>", self._on_language_changed)

        self.runtime_mode_label = ttk.Label(export_frame, text="")
        self.runtime_mode_label.grid(row=1, column=2, sticky=tk.W, padx=(12, 0), pady=(6, 0))
        self.runtime_mode_box = ttk.Combobox(
            export_frame,
            textvariable=self.runtime_mode_var,
            values=["normal", "strict"],
            state="readonly",
            width=12,
        )
        self.runtime_mode_box.grid(row=1, column=3, sticky=tk.W, padx=(8, 0), pady=(6, 0))
        self.runtime_mode_box.bind("<<ComboboxSelected>>", self._on_runtime_mode_changed)

        self.offline_check_btn = ttk.Button(export_frame, text="", command=self._check_offline_runtime)
        self.offline_check_btn.grid(row=1, column=4, sticky=tk.W, padx=(8, 0), pady=(6, 0))
        ttk.Label(export_frame, textvariable=self.offline_status_var).grid(row=1, column=5, sticky=tk.W, padx=(8, 0), pady=(6, 0))

        self.offline_health_btn = ttk.Button(export_frame, text="", command=self._check_offline_health)
        self.offline_health_btn.grid(row=1, column=8, sticky=tk.W, padx=(8, 0), pady=(6, 0))

        self.update_check_btn = ttk.Button(export_frame, text="", command=self._check_model_updates)
        self.update_check_btn.grid(row=1, column=6, sticky=tk.W, padx=(8, 0), pady=(6, 0))
        self.mark_updated_btn = ttk.Button(export_frame, text="", command=self._mark_model_updated)
        self.mark_updated_btn.grid(row=1, column=7, sticky=tk.W, padx=(8, 0), pady=(6, 0))
        ttk.Label(export_frame, textvariable=self.offline_health_var).grid(row=2, column=0, columnspan=9, sticky=tk.W, pady=(4, 0))
        ttk.Label(export_frame, textvariable=self.update_status_var).grid(row=3, column=0, columnspan=9, sticky=tk.W, pady=(2, 0))

        self.progress = ttk.Progressbar(root, mode="determinate", maximum=100, variable=self.progress_var)
        self.progress.grid(row=7, column=0, columnspan=3, sticky=tk.EW, pady=(16, 8))

        ttk.Label(root, textvariable=self.status_var).grid(row=8, column=0, columnspan=3, sticky=tk.W)

        self.preview_frame = ttk.LabelFrame(root, text="", padding=8)
        self.preview_frame.grid(row=9, column=0, columnspan=3, sticky=tk.NSEW, pady=(10, 0))
        self.preview_text = tk.Text(self.preview_frame, height=8, wrap=tk.WORD)
        self.preview_text.grid(row=0, column=0, sticky=tk.NSEW)
        preview_scroll = ttk.Scrollbar(self.preview_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        preview_scroll.grid(row=0, column=1, sticky=tk.NS)
        self.preview_text.configure(yscrollcommand=preview_scroll.set)
        self.preview_text.insert("1.0", "")
        self.preview_text.configure(state=tk.DISABLED)
        self.preview_frame.columnconfigure(0, weight=1)
        self.preview_frame.rowconfigure(0, weight=1)

        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)
        root.rowconfigure(9, weight=1)
        self._apply_language()
        self._refresh_cache_status()
        self._refresh_offline_status()
        self._refresh_offline_health_status()
        self._refresh_update_status()

    def _pick_file(self) -> None:
        initial_dir = self.upload_dir_var.get().strip() or "."
        file_paths = filedialog.askopenfilenames(
            title=ui_text(self.language_var.get(), "choose_audio_file"),
            initialdir=initial_dir,
            filetypes=[("Audio files", "*.mp3 *.wav"), ("All files", "*.*")],
        )
        if not file_paths:
            return

        valid_files, skipped_files, truncated_count = collect_batch_upload_files(tuple(file_paths), max_items=5)
        if not valid_files:
            messagebox.showwarning(
                ui_text(self.language_var.get(), "warning"),
                ui_text(self.language_var.get(), "batch_upload_no_valid"),
            )
            return

        first_file = valid_files[0].path
        self.selected_path.set(str(first_file))
        self.upload_dir_var.set(str(first_file.parent))
        self._save_ui_settings()
        self._refresh_uploads()

        messagebox.showinfo(
            ui_text(self.language_var.get(), "batch_upload_summary_title"),
            ui_text(self.language_var.get(), "batch_upload_summary_message").format(
                valid=len(valid_files),
                invalid=len(skipped_files),
                truncated=truncated_count,
            ),
        )

    def _refresh_uploads(self) -> None:
        source = self.selected_path.get().strip()
        if not source:
            messagebox.showinfo(
                ui_text(self.language_var.get(), "prompt"),
                ui_text(self.language_var.get(), "select_file_before_refresh"),
            )
            return

        upload_dir = Path(source).parent
        try:
            self.upload_items = list_recent_uploads(upload_dir=upload_dir, max_items=5)
        except Exception as exc:
            messagebox.showerror(ui_text(self.language_var.get(), "error"), str(exc))
            return

        self.upload_tree.delete(*self.upload_tree.get_children())
        for index, item in enumerate(self.upload_items):
            duration = "-" if item.duration_sec is None else f"{item.duration_sec:.2f}s"
            size_kb = f"{item.size_bytes / 1024:.1f}KB"
            self.upload_tree.insert("", tk.END, iid=str(index), values=(item.filename, size_kb, duration, item.extension))

        self.upload_hint.set(
            ui_text(self.language_var.get(), "upload_loaded_hint").format(upload_dir=upload_dir, count=len(self.upload_items))
        )

    def _selected_upload_item(self) -> AudioFileInfo | None:
        selected = self.upload_tree.selection()
        if not selected:
            return None
        idx = int(selected[0])
        if idx < 0 or idx >= len(self.upload_items):
            return None
        return self.upload_items[idx]

    def _on_upload_select(self, _event: object) -> None:
        item = self._selected_upload_item()
        if item is None:
            return
        self.selected_path.set(str(item.path))

    def _rename_selected_upload(self) -> None:
        item = self._selected_upload_item()
        if item is None:
            messagebox.showinfo(ui_text(self.language_var.get(), "prompt"), ui_text(self.language_var.get(), "select_upload_first"))
            return

        new_name = simpledialog.askstring(
            ui_text(self.language_var.get(), "rename"),
            ui_text(self.language_var.get(), "rename_prompt"),
            initialvalue=item.path.stem,
        )
        if new_name is None:
            return

        try:
            new_path = rename_uploaded_file(item.path, new_name)
        except Exception as exc:
            messagebox.showerror(ui_text(self.language_var.get(), "error"), str(exc))
            return

        self.selected_path.set(str(new_path))
        self._refresh_uploads()

    def _delete_selected_upload(self) -> None:
        item = self._selected_upload_item()
        if item is None:
            messagebox.showinfo(ui_text(self.language_var.get(), "prompt"), ui_text(self.language_var.get(), "select_upload_first"))
            return

        confirm = messagebox.askyesno(
            ui_text(self.language_var.get(), "confirm_delete"),
            ui_text(self.language_var.get(), "confirm_delete_message").format(filename=item.filename),
        )
        if not confirm:
            return

        try:
            delete_uploaded_file(item.path)
        except Exception as exc:
            messagebox.showerror(ui_text(self.language_var.get(), "error"), str(exc))
            return

        if self.selected_path.get().strip() == str(item.path):
            self.selected_path.set("")
        self._refresh_uploads()

    def _start_task(self) -> None:
        if self.current_future and not self.current_future.done():
            messagebox.showinfo(ui_text(self.language_var.get(), "prompt"), ui_text(self.language_var.get(), "task_running_tip"))
            return

        source = self.selected_path.get().strip()
        if not source:
            messagebox.showwarning(
                ui_text(self.language_var.get(), "warning"),
                ui_text(self.language_var.get(), "select_file_before_start"),
            )
            return

        self.status_var.set(ui_text(self.language_var.get(), "processing"))
        self.start_btn.configure(state=tk.DISABLED)
        self.cancel_btn.configure(state=tk.NORMAL)
        self.export_btn.configure(state=tk.DISABLED)
        self.progress_var.set(0)
        self._set_preview_text(ui_text(self.language_var.get(), "preview_loading"))
        os.environ["PIANOTRANS_STRICT_RUNTIME"] = "1" if self.runtime_mode_var.get() == "strict" else "0"

        offline_status = ensure_offline_cache_dirs(self.model_settings)
        self._refresh_offline_status(offline_status)
        if self.runtime_mode_var.get() == "strict" and not offline_status.all_cached:
            messagebox.showwarning(ui_text(self.language_var.get(), "warning"), ui_text(self.language_var.get(), "offline_strict_block"))
            self.status_var.set(ui_text(self.language_var.get(), "ready"))
            self.start_btn.configure(state=tk.NORMAL)
            self.cancel_btn.configure(state=tk.DISABLED)
            return

        def _on_progress(percent: int, stage: str, eta_sec: float | None) -> None:
            self.progress_updates.put((percent, stage, eta_sec))

        mode: TranscriptionMode = self.mode_var.get()  # type: ignore[assignment]
        self.current_future = self.queue_service.submit_transcription(
            Path(source),
            mode,
            progress_callback=_on_progress,
        )
        self.after(120, self._poll_future)

    def _on_mode_changed(self, _event: object) -> None:
        mode: TranscriptionMode = self.mode_var.get()  # type: ignore[assignment]
        self.mode_desc_var.set(mode_description_localized(mode, self.language_var.get()))
        try:
            save_last_mode(self.preference_file, mode)
        except OSError:
            # Preference write failures should not block primary flow.
            pass

    def _poll_future(self) -> None:
        if self.current_future is None:
            return

        self._drain_progress_updates()

        if not self.current_future.done():
            self.after(120, self._poll_future)
            return

        self.progress_var.set(100)
        self.start_btn.configure(state=tk.NORMAL)
        self.cancel_btn.configure(state=tk.DISABLED)

        try:
            result = self.current_future.result()
        except CancelledError:
            self.status_var.set(ui_text(self.language_var.get(), "task_cancelled"))
            return
        except Exception as exc:
            self.status_var.set(ui_text(self.language_var.get(), "task_failed"))
            messagebox.showerror(ui_text(self.language_var.get(), "error"), str(exc))
            return

        self.status_var.set(ui_text(self.language_var.get(), "completed").format(output_path=result.output_path))
        self.last_score = result.score
        self.processed_scores.append(result.score)
        self.export_btn.configure(state=tk.NORMAL)
        self.batch_export_btn.configure(state=tk.NORMAL)
        try:
            preview = load_score_preview(result.output_path)
        except OSError as exc:
            self._set_preview_text(ui_text(self.language_var.get(), "preview_load_failed").format(error=exc))
        else:
            self._set_preview_text(preview)
        messagebox.showinfo(
            ui_text(self.language_var.get(), "complete"),
            ui_text(self.language_var.get(), "complete_message").format(output_path=result.output_path),
        )

    def _drain_progress_updates(self) -> None:
        while True:
            try:
                percent, stage, eta_sec = self.progress_updates.get_nowait()
            except Empty:
                break
            self.progress_var.set(max(0, min(100, percent)))
            if eta_sec is not None:
                self.status_var.set(f"{stage} ({percent}%) | 预计剩余 {eta_sec:.1f}s")
            else:
                self.status_var.set(f"{stage} ({percent}%)")

    def _cancel_task(self) -> None:
        if self.current_future is None:
            return
        cancelled = self.queue_service.cancel_transcription(self.current_future)
        if cancelled:
            self.status_var.set(ui_text(self.language_var.get(), "task_cancelled"))
            self.cancel_btn.configure(state=tk.DISABLED)
            self.start_btn.configure(state=tk.NORMAL)
            self.progress_var.set(0)
            return
        messagebox.showinfo(ui_text(self.language_var.get(), "prompt"), ui_text(self.language_var.get(), "cancel_not_supported"))

    def _export_current_score(self) -> None:
        if self.last_score is None:
            messagebox.showinfo(ui_text(self.language_var.get(), "prompt"), ui_text(self.language_var.get(), "no_score_to_export"))
            return

        fmt = self.export_format_var.get().strip()
        output_dir = Path(self.export_dir_var.get().strip() or "./outputs")
        try:
            output_path = export_score(self.last_score, output_dir, fmt=fmt)
        except Exception as exc:
            messagebox.showerror(ui_text(self.language_var.get(), "error"), str(exc))
            return

        messagebox.showinfo(
            ui_text(self.language_var.get(), "export_success"),
            ui_text(self.language_var.get(), "export_success_message").format(output_path=output_path),
        )

    def _export_all_scores(self) -> None:
        if not self.processed_scores:
            messagebox.showinfo(ui_text(self.language_var.get(), "prompt"), ui_text(self.language_var.get(), "no_score_to_export"))
            return

        fmt = self.export_format_var.get().strip()
        output_dir = Path(self.export_dir_var.get().strip() or "./outputs")
        try:
            exported_paths = export_scores(self.processed_scores, output_dir, fmt=fmt)
        except Exception as exc:
            messagebox.showerror(ui_text(self.language_var.get(), "error"), str(exc))
            return

        messagebox.showinfo(
            ui_text(self.language_var.get(), "export_success"),
            ui_text(self.language_var.get(), "batch_export_success_message").format(
                count=len(exported_paths),
                output_dir=output_dir,
            ),
        )

    def _set_preview_text(self, text: str) -> None:
        if self.preview_text is None:
            return
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", text)
        self.preview_text.configure(state=tk.DISABLED)

    def _pick_export_dir(self) -> None:
        current = self.export_dir_var.get().strip() or "."
        selected = filedialog.askdirectory(title=ui_text(self.language_var.get(), "export_dir"), initialdir=current)
        if not selected:
            return
        self.export_dir_var.set(selected)
        self._save_ui_settings()

    def _on_export_setting_changed(self, _event: object) -> None:
        self._save_ui_settings()

    def _on_language_changed(self, _event: object) -> None:
        self._apply_language()
        self._save_ui_settings()

    def _on_runtime_mode_changed(self, _event: object) -> None:
        self._save_ui_settings()

    def _refresh_cache_status(self) -> None:
        status = get_cache_status(self.transcription_cache_dir)
        size_kb = status.total_size_bytes / 1024
        self.cache_status_var.set(
            ui_text(self.language_var.get(), "cache_status").format(count=status.file_count, size_kb=size_kb)
        )

    def _refresh_offline_status(self, status: OfflineRuntimeStatus | None = None) -> None:
        offline_status = status if status is not None else inspect_offline_runtime(self.model_settings)
        if offline_status.all_cached:
            self.offline_status_var.set(ui_text(self.language_var.get(), "offline_status_ready"))
            return
        missing_count = len(offline_status.missing_models)
        self.offline_status_var.set(ui_text(self.language_var.get(), "offline_status_missing").format(count=missing_count))

    def _check_offline_runtime(self) -> None:
        offline_status = inspect_offline_runtime(self.model_settings)
        self._refresh_offline_status(offline_status)
        if offline_status.all_cached:
            messagebox.showinfo(ui_text(self.language_var.get(), "complete"), ui_text(self.language_var.get(), "offline_ready_message"))
            return

        missing_detail = ", ".join(
            f"{item.name}: {item.path}" for item in offline_status.items if not item.cached
        )
        messagebox.showwarning(
            ui_text(self.language_var.get(), "warning"),
            ui_text(self.language_var.get(), "offline_missing_message").format(missing=missing_detail),
        )

    def _refresh_offline_health_status(self) -> None:
        report = get_offline_health_report(self.model_settings)
        if report.ready_for_offline:
            self.offline_health_var.set(ui_text(self.language_var.get(), "offline_health_ready"))
            return
        pending_count = len(report.missing_models) + len(report.pending_update_models)
        self.offline_health_var.set(
            ui_text(self.language_var.get(), "offline_health_not_ready").format(count=pending_count)
        )

    def _check_offline_health(self) -> None:
        report = get_offline_health_report(self.model_settings)
        self._refresh_offline_status(report.runtime_status)
        self._refresh_update_status()
        self._refresh_offline_health_status()
        if report.ready_for_offline:
            messagebox.showinfo(
                ui_text(self.language_var.get(), "complete"),
                ui_text(self.language_var.get(), "offline_health_ready_message"),
            )
            return

        details: list[str] = []
        if report.missing_models:
            details.append(f"missing_cache={', '.join(report.missing_models)}")
        if report.pending_update_models:
            details.append(f"pending_updates={', '.join(report.pending_update_models)}")
        messagebox.showwarning(
            ui_text(self.language_var.get(), "warning"),
            ui_text(self.language_var.get(), "offline_health_not_ready_message").format(details="\n".join(details)),
        )

    def _clear_cache(self) -> None:
        removed = clear_cache(self.transcription_cache_dir)
        self._refresh_cache_status()
        messagebox.showinfo(
            ui_text(self.language_var.get(), "cache_management"),
            ui_text(self.language_var.get(), "cache_cleared").format(removed=removed),
        )

    def _refresh_update_status(self) -> None:
        report = check_model_updates(self.model_settings)
        if report.has_updates:
            self.update_status_var.set(
                ui_text(self.language_var.get(), "update_status_pending").format(count=report.update_count)
            )
            return
        self.update_status_var.set(ui_text(self.language_var.get(), "update_status_latest"))

    def _check_model_updates(self) -> None:
        report = check_model_updates(self.model_settings)
        self._refresh_update_status()
        if not report.has_updates:
            messagebox.showinfo(ui_text(self.language_var.get(), "complete"), ui_text(self.language_var.get(), "update_latest_message"))
            return

        details = "\n".join(
            f"{item.name}: {item.installed_version or 'none'} -> {item.target_version} ({item.path})"
            for item in report.items
            if item.needs_update
        )
        messagebox.showwarning(
            ui_text(self.language_var.get(), "warning"),
            ui_text(self.language_var.get(), "update_pending_message").format(details=details),
        )

    def _mark_model_updated(self) -> None:
        model_name = simpledialog.askstring(
            ui_text(self.language_var.get(), "mark_updated"),
            ui_text(self.language_var.get(), "mark_update_hint"),
        )
        if model_name is None:
            return

        try:
            mark_model_updated(self.model_settings, model_name)
        except Exception as exc:
            messagebox.showerror(ui_text(self.language_var.get(), "error"), str(exc))
            return

        self._refresh_update_status()
        messagebox.showinfo(
            ui_text(self.language_var.get(), "complete"),
            ui_text(self.language_var.get(), "mark_update_success").format(model=model_name.strip().lower()),
        )

    def _apply_language(self) -> None:
        lang = self.language_var.get()
        self.audio_label.configure(text=ui_text(lang, "audio_file"))
        self.pick_file_btn.configure(text=ui_text(lang, "choose_file"))
        self.upload_frame.configure(text=ui_text(lang, "upload_list"))
        self.upload_tree.heading("name", text="Name" if lang == "en_US" else "文件名")
        self.upload_tree.heading("size", text="Size" if lang == "en_US" else "大小")
        self.upload_tree.heading("duration", text="Duration" if lang == "en_US" else "时长")
        self.upload_tree.heading("ext", text="Type" if lang == "en_US" else "格式")
        self.refresh_upload_btn.configure(text=ui_text(lang, "refresh"))
        self.rename_upload_btn.configure(text=ui_text(lang, "rename"))
        self.delete_upload_btn.configure(text=ui_text(lang, "delete"))
        if not self.selected_path.get().strip():
            self.upload_hint.set(ui_text(lang, "upload_hint_default"))

        self.mode_label.configure(text=ui_text(lang, "mode"))
        mode: TranscriptionMode = self.mode_var.get()  # type: ignore[assignment]
        self.mode_desc_var.set(mode_description_localized(mode, lang))
        self.start_btn.configure(text=ui_text(lang, "start"))
        self.cancel_btn.configure(text=ui_text(lang, "cancel"))

        self.export_format_label.configure(text=ui_text(lang, "export_format"))
        self.export_dir_label.configure(text=ui_text(lang, "export_dir"))
        self.pick_export_dir_btn.configure(text=ui_text(lang, "choose"))
        self.export_btn.configure(text=ui_text(lang, "export_current"))
        self.batch_export_btn.configure(text=ui_text(lang, "export_all"))
        self.clear_cache_btn.configure(text=ui_text(lang, "clear_cache"))
        self.language_label.configure(text=ui_text(lang, "language"))
        self.runtime_mode_label.configure(text=ui_text(lang, "runtime_mode"))
        self.offline_check_btn.configure(text=ui_text(lang, "offline_check"))
        self.offline_health_btn.configure(text=ui_text(lang, "offline_health_check"))
        self.update_check_btn.configure(text=ui_text(lang, "update_check"))
        self.mark_updated_btn.configure(text=ui_text(lang, "mark_updated"))

        self.preview_frame.configure(text=ui_text(lang, "preview"))
        if self.last_score is None:
            self._set_preview_text(ui_text(lang, "preview_placeholder"))
        if self.current_future is None or self.current_future.done():
            self.status_var.set(ui_text(lang, "ready"))
        self._refresh_offline_status()
        self._refresh_offline_health_status()
        self._refresh_update_status()

    def _save_ui_settings(self) -> None:
        settings = UiSettings(
            export_format=self.export_format_var.get().strip().lower() or "txt",
            export_dir=self.export_dir_var.get().strip() or "./outputs",
            upload_dir=self.upload_dir_var.get().strip() or ".",
            language=self.language_var.get().strip() or "zh_CN",
            runtime_mode=self.runtime_mode_var.get().strip().lower() or "normal",
        )
        try:
            save_ui_settings(self.ui_settings_file, settings)
        except OSError:
            pass

    def _on_close(self) -> None:
        self.queue_service.shutdown()
        self.destroy()


def main() -> int:
    configure_logging()
    app = DesktopApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
