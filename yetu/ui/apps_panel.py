# -*- coding: utf-8 -*-
"""面板二:已安装应用。"""
from __future__ import annotations

from tkinter import ttk, StringVar

from ..core.device import list_apps
from ..registry import register_panel
from .base import BasePanel


@register_panel(name="已装应用", order=20)
class AppsPanel(BasePanel):
    def _build(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=6, pady=6)

        self.refresh_btn = ttk.Button(bar, text="刷新", command=self.refresh)
        self.refresh_btn.pack(side="left")

        self.third_only = ttk.Checkbutton(
            bar, text="仅第三方应用", command=self.refresh
        )
        self.third_only.state(["selected"])  # 默认勾选
        self.third_only.pack(side="left", padx=8)

        ttk.Label(bar, text="搜索:").pack(side="left")
        self.search_var = StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        search = ttk.Entry(bar, textvariable=self.search_var, width=24)
        search.pack(side="left", padx=4)

        self.count_lbl = ttk.Label(bar, text="共 0 个")
        self.count_lbl.pack(side="right", padx=6)

        wrap = ttk.Frame(self)
        wrap.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        columns = ("pkg", "version")
        self.tree = ttk.Treeview(wrap, columns=columns, show="headings", height=12)
        self.tree.heading("pkg", text="包名")
        self.tree.heading("version", text="版本")
        self.tree.column("pkg", width=420, anchor="w")
        self.tree.column("version", width=120, anchor="w")

        scroll = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self._all_rows: list[tuple[str, str]] = []

    # ---------------- 行为 ----------------
    def on_device_changed(self, device) -> None:
        self.device = device
        self.refresh()

    def refresh(self) -> None:
        self._clear_rows()
        self.count_lbl.configure(text="共 0 个")
        if self.device is None:
            return
        third_only = "selected" in self.third_only.state()
        self.run_async(
            lambda: list_apps(self.device, third_party_only=third_only),
            self._show_apps,
            busy_widget=self.refresh_btn,
            busy_text="加载中…",
        )

    def _show_apps(self, rows) -> None:
        self._all_rows = rows
        self._apply_filter()

    def _apply_filter(self) -> None:
        self._clear_rows()
        keyword = self.search_var.get().strip().lower()
        shown = 0
        for pkg, ver in self._all_rows:
            if keyword and keyword not in pkg.lower():
                continue
            self.tree.insert("", "end", values=(pkg, ver))
            shown += 1
        self.count_lbl.configure(text=f"共 {shown} 个")

    def _clear_rows(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
