# -*- coding: utf-8 -*-
"""面板注册表:新增功能面板 = 新增一个 UI 类 + 注册,主窗口自动生成 Tab。

扩展方法:
    在 yetu/ui/xxx_panel.py 里:
        @register_panel(name="新功能", order=60)
        class XxxPanel(BasePanel):
            ...
    然后在 yetu/app.py 的 import 区加上这个模块即可(或放到自动加载列表)。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # 仅类型提示,避免运行时循环导入
    from .ui.base import BasePanel


class _PanelRegistry:
    def __init__(self) -> None:
        self._panels: list[type["BasePanel"]] = []

    def register(self, cls: type["BasePanel"]) -> type["BasePanel"]:
        self._panels.append(cls)
        # 按 order 排序,稳定插入
        self._panels.sort(key=lambda c: (getattr(c, "order", 100), getattr(c, "name", "")))
        return cls

    def all(self) -> list[type["BasePanel"]]:
        return list(self._panels)


_registry = _PanelRegistry()


def register_panel(name: str, order: int = 100):
    """装饰器:把面板类注册进注册表。name 用作 Tab 标题,order 控制排序。"""
    def deco(cls):
        cls.name = name
        cls.order = order
        return _registry.register(cls)
    return deco


def all_panels() -> list[type["BasePanel"]]:
    return _registry.all()
