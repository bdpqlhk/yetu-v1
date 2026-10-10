#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""野兔 入口。

开发运行:   python3 main.py
打包运行:   sh build.sh   (产物在 dist/)
"""
import sys
import os

# 保证在打包/以模块方式运行时能找到 yetu 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yetu.app import launch  # noqa: E402


def _selftest() -> None:
    """打包后自检:验证内置工具、面板、设备发现是否正常。"""
    from yetu.core.adb import list_all_devices
    from yetu.core.env import tool_status
    from yetu.registry import all_panels

    print("YETU_SELFTEST_START")
    print("tools:", tool_status())
    print("panels:", [p.name for p in all_panels()])
    try:
        devs = [(d.serial, t) for d, t in list_all_devices()]
        print("devices:", devs or "(none)")
    except Exception as e:  # noqa: BLE001
        print("devices: ERROR", e)
    print("YETU_SELFTEST_END")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        launch()
