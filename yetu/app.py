# -*- coding: utf-8 -*-
"""野兔主窗口:顶部设备选择 + 中部功能 Tab + 底部状态栏。"""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, StringVar

from . import ui as _ui  # noqa: F401  触发面板注册
from .core.adb import list_all_devices
from .core.device import Device, from_entry
from .core.env import tool_status
from .registry import all_panels


class YetuApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("野兔 · 手机调试工具箱")
        self.geometry("920x640")
        self.minsize(760, 520)

        self.current_device: Device | None = None
        self._devices: list[Device] = []
        self._panels = []

        self._build_toolbar()
        self._build_notebook()
        self._build_statusbar()

        # 启动后自动刷新设备列表
        self.after(300, self.refresh_devices)

    # ------------------------------------------------------------------ #
    # 界面搭建
    # ------------------------------------------------------------------ #
    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, padding=(6, 6))
        bar.pack(fill="x")

        ttk.Label(bar, text="设备:").pack(side="left")
        self.device_var = StringVar()
        self.device_combo = ttk.Combobox(
            bar, textvariable=self.device_var, width=48, state="readonly"
        )
        self.device_combo.pack(side="left", padx=6)
        self.device_combo.bind("<<ComboboxSelected>>", self._on_device_selected)

        self.refresh_dev_btn = ttk.Button(bar, text="刷新设备", command=self.refresh_devices)
        self.refresh_dev_btn.pack(side="left")

        self.tool_lbl = ttk.Label(bar, text="", foreground="#888")
        self.tool_lbl.pack(side="right")
        self._update_tool_label()

    def _build_notebook(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        for cls in all_panels():
            panel = cls(self.notebook, app=self)
            self._panels.append(panel)
            self.notebook.add(panel, text=panel.name)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _build_statusbar(self) -> None:
        self.status_lbl = ttk.Label(
            self, text="就绪", relief="sunken", anchor="w", padding=(6, 2)
        )
        self.status_lbl.pack(fill="x", side="bottom")

    def _update_tool_label(self) -> None:
        status = tool_status()
        parts = [f"adb: {'✓' if status['adb'] else '✗'}",
                 f"hdc: {'✓' if status['hdc'] else '✗'}"]
        self.tool_lbl.configure(text="  内置工具  " + "  ".join(parts))

    # ------------------------------------------------------------------ #
    # 设备管理
    # ------------------------------------------------------------------ #
    def refresh_devices(self) -> None:
        self.refresh_dev_btn.configure(state="disabled", text="刷新中…")
        self._async_call(list_all_devices, self._on_devices_loaded)

    def _on_devices_loaded(self, result) -> None:
        self.refresh_dev_btn.configure(state="normal", text="刷新设备")
        if isinstance(result, BaseException):
            self.show_status(f"读取设备失败: {result}", error=True)
            return

        self._devices = [from_entry(entry, transport) for entry, transport in result]
        labels = [d.label for d in self._devices]
        self.device_combo.configure(values=labels)

        # 保留当前选择;否则默认选第一台
        if not labels:
            self.device_combo.set("")
            self._select_device(None)
        else:
            if self.current_device:
                keep = self.current_device.serial
                for i, d in enumerate(self._devices):
                    if d.serial == keep and d.transport == self.current_device.transport:
                        self.device_combo.current(i)
                        self._select_device(d)
                        break
                else:
                    self.device_combo.current(0)
                    self._select_device(self._devices[0])
            else:
                self.device_combo.current(0)
                self._select_device(self._devices[0])

    def _on_device_selected(self, _event=None) -> None:
        idx = self.device_combo.current()
        dev = self._devices[idx] if 0 <= idx < len(self._devices) else None
        self._select_device(dev)

    def _select_device(self, dev: Device | None) -> None:
        self.current_device = dev
        if dev is None:
            self.show_status("未连接设备 — 请用数据线连接手机并开启 USB 调试", error=True)
        else:
            kind = "鸿蒙" if dev.is_hdc else "安卓"
            self.show_status(f"已连接 {dev.serial} ({kind})")
        for panel in self._panels:
            panel.on_device_changed(dev)

    # ------------------------------------------------------------------ #
    # Tab 切换:自动刷新当前面板
    # ------------------------------------------------------------------ #
    def _on_tab_changed(self, _event=None) -> None:
        try:
            idx = self.notebook.index(self.notebook.select())
            panel = self._panels[idx]
            if self.current_device is not None:
                panel.refresh()
        except tk.TclError:
            pass

    # ------------------------------------------------------------------ #
    # 通用工具
    # ------------------------------------------------------------------ #
    def _async_call(self, fn, on_done) -> None:
        def worker() -> None:
            try:
                result = fn()
            except BaseException as e:  # noqa: BLE001
                result = e
            self.after(0, lambda: on_done(result))

        threading.Thread(target=worker, daemon=True).start()

    def show_status(self, msg: str, error: bool = False) -> None:
        try:
            self.status_lbl.configure(
                text=msg, foreground="#c0392b" if error else "#333333"
            )
        except tk.TclError:
            pass


def launch() -> None:
    app = YetuApp()
    app.mainloop()
