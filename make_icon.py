#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「野兔」应用图标 (assets/icon.icns)。

一次运行: python3 make_icon.py
产物: assets/icon.icns(供 PyInstaller --icon 使用)
"""
import os
import subprocess

from PIL import Image, ImageDraw

SIZE = 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
ICONSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.iconset")


def rounded_rect_mask(draw, box, radius):
    draw.rounded_rectangle(box, radius=radius, fill="white")


def draw_rabbit(draw):
    """在 1024x1024 画布上画一只简笔小兔子。"""
    # 绿色渐变圆角底(左上 → 右下 两种绿色分块,做成近似渐变)
    for i in range(SIZE):
        t = i / SIZE
        r = int(88 + (36 - 88) * t)
        g = int(150 + (90 - 150) * t)
        b = int(80 + (46 - 80) * t)
        draw.line([(0, i), (SIZE, i)], fill=(r, g, b, 255))
    # 白色圆角遮罩外框
    mask = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([40, 40, SIZE - 40, SIZE - 40], radius=200, fill=(0, 0, 0, 255))
    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    bd = ImageDraw.Draw(base)
    bd.rounded_rectangle([40, 40, SIZE - 40, SIZE - 40], radius=200, fill=(255, 255, 255, 255))
    # 耳朵(两个竖椭圆)
    def ear(cx, tilt):
        ox = 1 if tilt > 0 else -1
        bd.ellipse([cx - 110, 180, cx + 110, 620], fill=(255, 255, 255, 255))
        bd.ellipse([cx - 55 + ox * 10, 260, cx + 55 + ox * 10, 540], fill=(250, 200, 205, 255))
    ear(300, -1)
    ear(724, 1)
    # 脸
    bd.ellipse([180, 380, 844, 900], fill=(255, 255, 255, 255))
    # 眼睛
    bd.ellipse([340, 570, 430, 660], fill=(30, 30, 30, 255))
    bd.ellipse([594, 570, 684, 660], fill=(30, 30, 30, 255))
    bd.ellipse([366, 596, 404, 634], fill=(255, 255, 255, 255))
    bd.ellipse([620, 596, 658, 634], fill=(255, 255, 255, 255))
    # 鼻子
    bd.polygon([(482, 700), (542, 700), (512, 748)], fill=(245, 130, 140, 255))
    # 嘴
    bd.line([(512, 748), (512, 780)], fill=(60, 60, 60, 255), width=12)
    bd.arc([420, 760, 512, 830], start=0, end=180, fill=(60, 60, 60, 255), width=12)
    bd.arc([512, 760, 604, 830], start=0, end=180, fill=(60, 60, 60, 255), width=12)
    # 腮红
    bd.ellipse([250, 700, 340, 780], fill=(255, 210, 210, 200))
    bd.ellipse([684, 700, 774, 780], fill=(255, 210, 210, 200))
    # 用遮罩裁出圆角底
    return Image.composite(base, Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0)), mask)


def main() -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    img = draw_rabbit(ImageDraw.Draw(img) or img)
    # 上面 draw_rabbit 需要 base 与 mask,重写更清晰的做法:
    # 直接在 img 上画
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for i in range(SIZE):  # 渐变底
        t = i / SIZE
        r = int(88 + (36 - 88) * t)
        g = int(150 + (90 - 150) * t)
        b = int(80 + (46 - 80) * t)
        draw.line([(0, i), (SIZE, i)], fill=(r, g, b, 255))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle([40, 40, SIZE - 40, SIZE - 40], radius=200, fill=255)
    img.putalpha(mask)

    d = ImageDraw.Draw(img)
    # 耳朵
    def ear(cx, ox):
        d.ellipse([cx - 110, 180, cx + 110, 620], fill=(255, 255, 255, 255))
        d.ellipse([cx - 55 + ox * 8, 260, cx + 55 + ox * 8, 540], fill=(250, 200, 205, 255))
    ear(300, -1)
    ear(724, 1)
    # 脸
    d.ellipse([180, 380, 844, 900], fill=(255, 255, 255, 255))
    # 眼睛
    d.ellipse([340, 570, 430, 660], fill=(30, 30, 30, 255))
    d.ellipse([594, 570, 684, 660], fill=(30, 30, 30, 255))
    d.ellipse([366, 596, 404, 634], fill=(255, 255, 255, 255))
    d.ellipse([620, 596, 658, 634], fill=(255, 255, 255, 255))
    # 鼻子 + 嘴
    d.polygon([(482, 700), (542, 700), (512, 748)], fill=(245, 130, 140, 255))
    d.line([(512, 748), (512, 782)], fill=(60, 60, 60, 255), width=12)
    d.arc([420, 760, 512, 832], start=0, end=180, fill=(60, 60, 60, 255), width=12)
    d.arc([512, 760, 604, 832], start=0, end=180, fill=(60, 60, 60, 255), width=12)
    # 腮红
    d.ellipse([250, 700, 340, 780], fill=(255, 210, 210, 200))
    d.ellipse([684, 700, 774, 780], fill=(255, 210, 210, 200))

    img.save(OUT)
    print("PNG 生成:", OUT)

    # 生成 .icns(iconutil 需 iconset 目录)
    if os.path.exists(ICONSET):
        subprocess.run(["rm", "-rf", ICONSET], check=True)
    os.makedirs(ICONSET, exist_ok=True)
    sizes = [(16, "icon_16x16.png"), (32, "icon_32x32.png"), (128, "icon_128x128.png"),
             (256, "icon_256x256.png"), (512, "icon_512x512.png")]
    for px, name in sizes:
        img.resize((px, px), Image.LANCZOS).save(os.path.join(ICONSET, name))
        img.resize((px * 2, px * 2), Image.LANCZOS).save(
            os.path.join(ICONSET, name.replace(".png", "@2x.png")))
    icns = os.path.join(os.path.dirname(ICONSET), "icon.icns")
    subprocess.run(["iconutil", "-c", "icns", ICONSET, "-o", icns], check=True)
    print("ICNS 生成:", icns)


if __name__ == "__main__":
    main()
