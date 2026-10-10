# -*- coding: utf-8 -*-
"""面板三:网络信息。"""
from __future__ import annotations

from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from ..core.device import get_network_text
from ..registry import register_panel
from .base import BasePanel


@register_panel(name="网络信息", order=30)
class NetworkPanel(BasePanel):
    def _build(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=6, pady=6)
        self.refresh_btn = ttk.Button(bar, text="刷新网络信息", command=self.refresh)
        self.refresh_btn.pack(side="left")

        self.text = ScrolledText(self, height=18, wrap="word", state="disabled", font=("Menlo", 11))
        self.text.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    # ---------------- 行为 ----------------
    def on_device_changed(self, device) -> None:
        self.device = device
        self.refresh()

    def refresh(self) -> None:
        if self.device is None:
            self._set_text("未连接设备")
            return
        self._set_text("正在读取网络信息 …")
        self.run_async(
            lambda: get_network_text(self.device),
            self._set_text,
            busy_widget=self.refresh_btn,
            busy_text="读取中…",
        )

    def _set_text(self, content: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.configure(state="disabled")
