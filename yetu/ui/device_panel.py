# -*- coding: utf-8 -*-
"""面板一:手机信息。"""
from __future__ import annotations

from tkinter import ttk

from ..core.device import get_device_info
from ..registry import register_panel
from .base import BasePanel


@register_panel(name="手机信息", order=10)
class DevicePanel(BasePanel):
    def _build(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=6, pady=6)
        self.refresh_btn = ttk.Button(bar, text="刷新信息", command=self.refresh)
        self.refresh_btn.pack(side="left")
        self.hint = ttk.Label(bar, text="", foreground="#888")
        self.hint.pack(side="left", padx=8)

        wrap = ttk.Frame(self)
        wrap.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        columns = ("key", "value")
        self.tree = ttk.Treeview(wrap, columns=columns, show="headings", height=12)
        self.tree.heading("key", text="属性")
        self.tree.heading("value", text="值")
        self.tree.column("key", width=140, anchor="w")
        self.tree.column("value", width=460, anchor="w")

        scroll = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    # ---------------- 行为 ----------------
    def on_device_changed(self, device) -> None:
        self.device = device
        self.refresh()

    def refresh(self) -> None:
        self._clear_rows()
        if self.device is None:
            self.hint.configure(text="未连接设备")
            return
        self.hint.configure(text=f"正在读取 {self.device.serial} …")
        self.run_async(
            lambda: get_device_info(self.device),
            self._show_info,
            busy_widget=self.refresh_btn,
            busy_text="读取中…",
        )

    def _show_info(self, rows) -> None:
        self.hint.configure(text="")
        for key, value in rows:
            self.tree.insert("", "end", values=(key, value))
        if not rows:
            self.hint.configure(text="未读取到信息")

    def _clear_rows(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
