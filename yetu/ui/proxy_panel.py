# -*- coding: utf-8 -*-
"""面板四:全局代理设置 / 清除。"""
from __future__ import annotations

from tkinter import ttk, StringVar

from ..core.device import clear_proxy, get_proxy, set_proxy
from ..registry import register_panel
from .base import BasePanel


@register_panel(name="全局代理", order=40)
class ProxyPanel(BasePanel):
    def _build(self) -> None:
        pad = {"padx": 8, "pady": 6}

        box = ttk.LabelFrame(self, text="设置 / 清除全局代理")
        box.pack(fill="x", padx=6, pady=6)

        row1 = ttk.Frame(box)
        row1.pack(fill="x", **pad)
        ttk.Label(row1, text="当前代理:").pack(side="left")
        self.current_lbl = ttk.Label(row1, text="—", foreground="#666")
        self.current_lbl.pack(side="left", padx=6)
        ttk.Button(row1, text="读取当前代理", command=self.refresh).pack(side="left", padx=6)

        row2 = ttk.Frame(box)
        row2.pack(fill="x", **pad)
        ttk.Label(row2, text="主机:").pack(side="left")
        self.host_var = StringVar()
        ttk.Entry(row2, textvariable=self.host_var, width=20).pack(side="left", padx=4)
        ttk.Label(row2, text="端口:").pack(side="left", padx=(12, 0))
        self.port_var = StringVar()
        ttk.Entry(row2, textvariable=self.port_var, width=8).pack(side="left", padx=4)

        row3 = ttk.Frame(box)
        row3.pack(fill="x", **pad)
        self.set_btn = ttk.Button(row3, text="设置代理", command=self._on_set)
        self.set_btn.pack(side="left", padx=4)
        self.clear_btn = ttk.Button(row3, text="清除代理", command=self._on_clear)
        self.clear_btn.pack(side="left", padx=4)

        tip = ttk.Label(
            self,
            text="提示:设置全局代理后,设备的 http/https 流量将走该代理(如 Charles、mitmproxy 抓包)。",
            foreground="#888",
        )
        tip.pack(fill="x", padx=8, pady=4)

    # ---------------- 行为 ----------------
    def on_device_changed(self, device) -> None:
        self.device = device
        self.refresh()

    def refresh(self) -> None:
        if self.device is None:
            self.current_lbl.configure(text="未连接设备")
            return
        self.run_async(lambda: get_proxy(self.device), self._show_current,
                       busy_widget=self.current_lbl, busy_text="读取中 …")

    def _show_current(self, value: str) -> None:
        self.current_lbl.configure(text=value)

    def _on_set(self) -> None:
        if self.device is None:
            self.show_error("未连接设备")
            return
        host = self.host_var.get().strip()
        port = self.port_var.get().strip()
        if not host or not port:
            self.show_error("请填写代理主机和端口")
            return
        self.set_btn.configure(state="disabled")
        self.run_async(
            lambda: set_proxy(self.device, host, port) or f"已设置代理 {host}:{port}",
            lambda msg: (self._show_current(f"{host}:{port}"), self.show_ok(msg)),
            busy_widget=self.set_btn,
        )

    def _on_clear(self) -> None:
        if self.device is None:
            self.show_error("未连接设备")
            return
        self.clear_btn.configure(state="disabled")
        self.run_async(
            lambda: clear_proxy(self.device) or "已清除全局代理",
            lambda msg: (self._show_current("(未设置)"), self.show_ok(msg)),
            busy_widget=self.clear_btn,
        )
