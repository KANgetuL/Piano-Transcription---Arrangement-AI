from __future__ import annotations

import tkinter as tk
from concurrent.futures import CancelledError
from concurrent.futures import Future
from pathlib import Path
from queue import Empty, SimpleQueue
from tkinter import filedialog, messagebox, simpledialog, ttk

from src.app.upload_workflow import delete_uploaded_file, list_recent_uploads, rename_uploaded_file
from src.services.mode_preference_service import load_last_mode, mode_description, save_last_mode
from src.models.entities import AudioFileInfo
from src.models.entities import TranscriptionMode
from src.services.score_preview_service import load_score_preview
from src.services.task_queue_service import TaskQueueService
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
        initial_mode = load_last_mode(self.preference_file)
        self.mode_var = tk.StringVar(value=initial_mode)
        self.status_var = tk.StringVar(value="就绪")
        self.progress_var = tk.IntVar(value=0)
        self.mode_desc_var = tk.StringVar(value=mode_description(initial_mode))
        self.upload_items: list[AudioFileInfo] = []
        self.progress_updates: SimpleQueue[tuple[int, str, float | None]] = SimpleQueue()
        self.preview_text: tk.Text | None = None

        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)

        ttk.Label(root, text="音频文件").grid(row=0, column=0, sticky=tk.W)
        entry = ttk.Entry(root, textvariable=self.selected_path, width=70)
        entry.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(4, 10))

        ttk.Button(root, text="选择文件", command=self._pick_file).grid(row=2, column=0, sticky=tk.W)

        upload_frame = ttk.LabelFrame(root, text="上传文件列表（最近 5 个）", padding=8)
        upload_frame.grid(row=3, column=0, columnspan=3, sticky=tk.NSEW, pady=(14, 0))

        self.upload_tree = ttk.Treeview(
            upload_frame,
            columns=("name", "size", "duration", "ext"),
            show="headings",
            height=5,
        )
        self.upload_tree.heading("name", text="文件名")
        self.upload_tree.heading("size", text="大小")
        self.upload_tree.heading("duration", text="时长")
        self.upload_tree.heading("ext", text="格式")
        self.upload_tree.column("name", width=320, anchor=tk.W)
        self.upload_tree.column("size", width=90, anchor=tk.E)
        self.upload_tree.column("duration", width=90, anchor=tk.E)
        self.upload_tree.column("ext", width=70, anchor=tk.CENTER)
        self.upload_tree.grid(row=0, column=0, columnspan=4, sticky=tk.NSEW)
        self.upload_tree.bind("<<TreeviewSelect>>", self._on_upload_select)

        ttk.Button(upload_frame, text="刷新", command=self._refresh_uploads).grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Button(upload_frame, text="重命名", command=self._rename_selected_upload).grid(
            row=1, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )
        ttk.Button(upload_frame, text="删除", command=self._delete_selected_upload).grid(
            row=1, column=2, sticky=tk.W, padx=(8, 0), pady=(8, 0)
        )
        upload_frame.columnconfigure(0, weight=1)

        self.upload_hint = tk.StringVar(value="请选择文件后可查看并管理最近上传记录")
        ttk.Label(upload_frame, textvariable=self.upload_hint).grid(row=1, column=3, sticky=tk.E, padx=(8, 0), pady=(8, 0))

        ttk.Label(root, text="模式").grid(row=4, column=0, sticky=tk.W, pady=(16, 0))
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

        self.progress = ttk.Progressbar(root, mode="determinate", maximum=100, variable=self.progress_var)
        self.progress.grid(row=6, column=0, columnspan=3, sticky=tk.EW, pady=(24, 8))

        ttk.Label(root, textvariable=self.status_var).grid(row=7, column=0, columnspan=3, sticky=tk.W)

        preview_frame = ttk.LabelFrame(root, text="乐谱预览（文本）", padding=8)
        preview_frame.grid(row=8, column=0, columnspan=3, sticky=tk.NSEW, pady=(10, 0))
        self.preview_text = tk.Text(preview_frame, height=8, wrap=tk.WORD)
        self.preview_text.grid(row=0, column=0, sticky=tk.NSEW)
        preview_scroll = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        preview_scroll.grid(row=0, column=1, sticky=tk.NS)
        self.preview_text.configure(yscrollcommand=preview_scroll.set)
        self.preview_text.insert("1.0", "处理完成后将显示导出文本内容。")
        self.preview_text.configure(state=tk.DISABLED)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)
        root.rowconfigure(8, weight=1)

    def _pick_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="选择音频文件",
            filetypes=[("Audio files", "*.mp3 *.wav"), ("All files", "*.*")],
        )
        if file_path:
            self.selected_path.set(file_path)
            self._refresh_uploads()

    def _refresh_uploads(self) -> None:
        source = self.selected_path.get().strip()
        if not source:
            messagebox.showinfo("提示", "请先选择音频文件后再刷新上传列表。")
            return

        upload_dir = Path(source).parent
        try:
            self.upload_items = list_recent_uploads(upload_dir=upload_dir, max_items=5)
        except Exception as exc:
            messagebox.showerror("错误", str(exc))
            return

        self.upload_tree.delete(*self.upload_tree.get_children())
        for index, item in enumerate(self.upload_items):
            duration = "-" if item.duration_sec is None else f"{item.duration_sec:.2f}s"
            size_kb = f"{item.size_bytes / 1024:.1f}KB"
            self.upload_tree.insert("", tk.END, iid=str(index), values=(item.filename, size_kb, duration, item.extension))

        self.upload_hint.set(f"当前目录: {upload_dir} | 已加载 {len(self.upload_items)} 条")

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
            messagebox.showinfo("提示", "请先在列表中选择一个文件。")
            return

        new_name = simpledialog.askstring("重命名", "输入新文件名（可不带后缀）", initialvalue=item.path.stem)
        if new_name is None:
            return

        try:
            new_path = rename_uploaded_file(item.path, new_name)
        except Exception as exc:
            messagebox.showerror("错误", str(exc))
            return

        self.selected_path.set(str(new_path))
        self._refresh_uploads()

    def _delete_selected_upload(self) -> None:
        item = self._selected_upload_item()
        if item is None:
            messagebox.showinfo("提示", "请先在列表中选择一个文件。")
            return

        confirm = messagebox.askyesno("确认删除", f"确定删除文件: {item.filename} ?")
        if not confirm:
            return

        try:
            delete_uploaded_file(item.path)
        except Exception as exc:
            messagebox.showerror("错误", str(exc))
            return

        if self.selected_path.get().strip() == str(item.path):
            self.selected_path.set("")
        self._refresh_uploads()

    def _start_task(self) -> None:
        if self.current_future and not self.current_future.done():
            messagebox.showinfo("提示", "已有任务在运行，请稍候。")
            return

        source = self.selected_path.get().strip()
        if not source:
            messagebox.showwarning("提示", "请先选择音频文件。")
            return

        self.status_var.set("处理中...")
        self.start_btn.configure(state=tk.DISABLED)
        self.cancel_btn.configure(state=tk.NORMAL)
        self.progress_var.set(0)
        self._set_preview_text("处理中，完成后将加载导出预览。")

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
        self.mode_desc_var.set(mode_description(mode))
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
            self.status_var.set("任务已取消")
            return
        except Exception as exc:
            self.status_var.set("处理失败")
            messagebox.showerror("错误", str(exc))
            return

        self.status_var.set(f"完成: {result.output_path}")
        try:
            preview = load_score_preview(result.output_path)
        except OSError as exc:
            self._set_preview_text(f"预览加载失败: {exc}")
        else:
            self._set_preview_text(preview)
        messagebox.showinfo("完成", f"导出文件: {result.output_path}")

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
            self.status_var.set("任务已取消")
            self.cancel_btn.configure(state=tk.DISABLED)
            self.start_btn.configure(state=tk.NORMAL)
            self.progress_var.set(0)
            return
        messagebox.showinfo("提示", "任务已开始执行，当前版本暂不支持中途取消。")

    def _set_preview_text(self, text: str) -> None:
        if self.preview_text is None:
            return
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", text)
        self.preview_text.configure(state=tk.DISABLED)

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
