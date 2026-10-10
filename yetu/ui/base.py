# -*- coding: utf-8 -*-
"""面板基类 + 线程安全的后台执行辅助。

后台执行约定:
    tkinter 不是线程安全的,所有耗时操作(adb/hdc 命令)放后台线程,
    完成后通过 root.after 回到主线程再更新控件。
"""
from __future__ import annotations

import threading
import traceback
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..app import YetuApp


class BasePanel(ttk.Frame):
    """所有功能面板的基类。

    子类只需:
        @register_panel(name="标题", order=50)
        class MyPanel(BasePanel):
            def _build(self): ...            # 搭界面
            def on_device_changed(self, device): ...  # 设备切换时
            def refresh(self): ...           # 点「刷新」按钮时
    """

    name = "未命名"
    order = 100

    def __init__(self, master, app: "YetuApp", **kw):
        super().__init__(master, **kw)
        self.app = app
        self.device = None  # 当前设备(由主窗口注入)
        self._build()

    # ---------------- 子类可覆写 ----------------
    def _build(self) -> None:
        """搭建本面板界面。"""

    def on_device_changed(self, device) -> None:
        """设备切换或刷新后回调。默认什么都不做。"""

    def refresh(self) -> None:
        """用户点「刷新」时调用。默认只做设备变更刷新。"""

    # ---------------- 通用工具 ----------------
    def run_async(self, fn: Callable[[], object], on_done: Callable[[object], None],
                  busy_widget=None, busy_text: str = "执行中…") -> None:
        """后台执行 fn,完成后在主线程回调 on_done(result)。

        可选 busy_widget:执行期间禁用某个控件(如刷新按钮),防止重复点击。
        """
        if busy_widget is not None:
            self._set_busy(busy_widget, True, busy_text)

        def worker() -> None:
            try:
                result = fn()
            except Exception as e:  # noqa: BLE001
                traceback.print_exc()
                result = e
            self._post(lambda: self._finish(result, on_done, busy_widget))

        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, result, on_done, busy_widget) -> None:
        if busy_widget is not None:
            self._set_busy(busy_widget, False)
        if isinstance(result, BaseException):
            self.show_error(f"{result}")
        else:
            on_done(result)

    @staticmethod
    def _set_busy(widget, busy: bool, text: str = "") -> None:
        try:
            widget.configure(state="disabled" if busy else "normal")
            if hasattr(widget, "configure") and "text" in widget.configure():
                if busy:
                    # 记住原始文字,busy 结束后还原,避免按钮一直停在「加载中…」
                    widget._yetu_busy_text = widget.cget("text")
                    widget.configure(text=text)
                else:
                    orig = getattr(widget, "_yetu_busy_text", None)
                    if orig is not None:
                        widget.configure(text=orig)
        except tk.TclError:
            pass

    def _post(self, fn: Callable[[], None]) -> None:
        """安全地回主线程执行;控件已销毁则跳过。"""
        try:
            if self.winfo_exists():
                self.after(0, fn)
        except tk.TclError:
            pass

    # ---------------- 提示 ----------------
    def show_error(self, msg: str) -> None:
        self.app.show_status(f"✗ {msg}", error=True)

    def show_ok(self, msg: str) -> None:
        self.app.show_status(f"✓ {msg}")

    def show_info(self, msg: str) -> None:
        self.app.show_status(msg)
