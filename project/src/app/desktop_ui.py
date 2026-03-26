from __future__ import annotations

import tkinter as tk
from concurrent.futures import Future
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.models.entities import TranscriptionMode
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
        self.mode_var = tk.StringVar(value="normal")
        self.status_var = tk.StringVar(value="就绪")

        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)

        ttk.Label(root, text="音频文件").grid(row=0, column=0, sticky=tk.W)
        entry = ttk.Entry(root, textvariable=self.selected_path, width=70)
        entry.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(4, 10))

        ttk.Button(root, text="选择文件", command=self._pick_file).grid(row=2, column=0, sticky=tk.W)

        ttk.Label(root, text="模式").grid(row=3, column=0, sticky=tk.W, pady=(16, 0))
        mode_box = ttk.Combobox(
            root,
            textvariable=self.mode_var,
            values=["normal", "pop", "electronic", "classical", "black"],
            state="readonly",
            width=22,
        )
        mode_box.grid(row=4, column=0, sticky=tk.W, pady=(4, 0))

        self.start_btn = ttk.Button(root, text="开始处理", command=self._start_task)
        self.start_btn.grid(row=4, column=1, sticky=tk.W, padx=(12, 0), pady=(4, 0))

        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.grid(row=5, column=0, columnspan=3, sticky=tk.EW, pady=(24, 8))

        ttk.Label(root, textvariable=self.status_var).grid(row=6, column=0, columnspan=3, sticky=tk.W)

        root.columnconfigure(0, weight=1)

    def _pick_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="选择音频文件",
            filetypes=[("Audio files", "*.mp3 *.wav"), ("All files", "*.*")],
        )
        if file_path:
            self.selected_path.set(file_path)

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
        self.progress.start(10)

        mode: TranscriptionMode = self.mode_var.get()  # type: ignore[assignment]
        self.current_future = self.queue_service.submit_transcription(Path(source), mode)
        self.after(120, self._poll_future)

    def _poll_future(self) -> None:
        if self.current_future is None:
            return

        if not self.current_future.done():
            self.after(120, self._poll_future)
            return

        self.progress.stop()
        self.start_btn.configure(state=tk.NORMAL)

        try:
            result = self.current_future.result()
        except Exception as exc:
            self.status_var.set("处理失败")
            messagebox.showerror("错误", str(exc))
            return

        self.status_var.set(f"完成: {result.output_path}")
        messagebox.showinfo("完成", f"导出文件: {result.output_path}")

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
