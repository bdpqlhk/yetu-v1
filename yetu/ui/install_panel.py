# -*- coding: utf-8 -*-
"""面板五:安装 APK / HAP。

- APK(安卓)走 adb install;HAP(鸿蒙)走 hdc install。
- 安装进度在下方文本框流式显示。
"""
from __future__ import annotations

import os
from tkinter import filedialog, ttk, StringVar

from ..core.adb import Adb, Hdc
from ..core.env import tool_status
from ..registry import register_panel
from .base import BasePanel

_EXT_LABEL = {".apk": "安卓 APK", ".hap": "鸿蒙 HAP"}
_EXT_BY_CONN = {".apk": "adb", ".hap": "hdc"}


@register_panel(name="安装应用", order=50)
class InstallPanel(BasePanel):
    def _build(self) -> None:
        box = ttk.LabelFrame(self, text="安装包")
        box.pack(fill="x", padx=6, pady=6)

        row1 = ttk.Frame(box)
        row1.pack(fill="x", padx=8, pady=6)
        self.file_var = StringVar()
        ttk.Entry(row1, textvariable=self.file_var, width=52).pack(side="left")
        ttk.Button(row1, text="选择文件…", command=self._browse).pack(side="left", padx=6)

        row2 = ttk.Frame(box)
        row2.pack(fill="x", padx=8, pady=(0, 6))
        self.install_btn = ttk.Button(row2, text="开始安装", command=self._install)
        self.install_btn.pack(side="left")
        self.detail_lbl = ttk.Label(row2, text="未选择安装包", foreground="#888")
        self.detail_lbl.pack(side="left", padx=8)

        tip = ttk.Label(
            self,
            text="提示:.apk 需要设备通过 adb 连接;.hap 需要设备通过 hdc 连接(鸿蒙)。",
            foreground="#888",
        )
        tip.pack(fill="x", padx=8, pady=4)

        from tkinter.scrolledtext import ScrolledText
        self.log = ScrolledText(self, height=14, wrap="word", state="disabled",
                                font=("Menlo", 10))
        self.log.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    # ---------------- 文件选择 ----------------
    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title="选择安装包",
            filetypes=[("安卓/鸿蒙安装包", "*.apk *.hap"), ("APK", "*.apk"), ("HAP", "*.hap")],
        )
        if not path:
            return
        self.file_var.set(path)
        ext = os.path.splitext(path)[1].lower()
        if ext in _EXT_LABEL:
            self.detail_lbl.configure(text=f"已识别: {_EXT_LABEL[ext]} ({os.path.basename(path)})")
        else:
            self.detail_lbl.configure(text="⚠ 不支持的文件类型,请选择 .apk 或 .hap")

    # ---------------- 安装 ----------------
    def _install(self) -> None:
        if self.device is None:
            self.show_error("请先在顶部选择已连接的设备")
            return
        path = self.file_var.get().strip()
        if not path or not os.path.isfile(path):
            self.show_error("请先选择一个有效的安装包文件")
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in _EXT_LABEL:
            self.show_error("仅支持 .apk / .hap 安装包")
            return

        need = _EXT_BY_CONN[ext]
        status = tool_status()
        if not status.get(need):
            self.show_error(f"工具内未找到 {need},无法安装 {_EXT_LABEL[ext]}")
            return

        conn = Adb() if need == "adb" else Hdc()
        self._append_log(f"▶ 开始安装 {_EXT_LABEL[ext]}: {os.path.basename(path)}\n")
        self._append_log(f"  目标设备: {self.device.label}\n\n")

        # 流式行回调来自工作线程,先回主线程再写文本框
        on_line = lambda line: self._post(lambda: self._append_log(line + "\n"))

        self.run_async(
            lambda: conn.install(self.device.serial, path, on_line=on_line),
            lambda proc: self._on_done(proc, ext),
            busy_widget=self.install_btn,
            busy_text="安装中…",
        )

    def _on_done(self, proc, ext: str) -> None:
        if proc.returncode == 0:
            self._append_log(f"\n✅ {_EXT_LABEL[ext]} 安装成功\n")
            self.show_ok(f"{_EXT_LABEL[ext]} 安装成功")
        else:
            # 流式输出已在日志里,这里补一句结论
            self._append_log(f"\n❌ 安装失败 (退出码 {proc.returncode})\n")
            self.show_error(f"{_EXT_LABEL[ext]} 安装失败")

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")
