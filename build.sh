#!/bin/bash
# 野兔 打包脚本 —— PyInstaller(macOS 通用)
# 产物:dist/野兔.app
set -e
cd "$(dirname "$0")"

NAME="野兔"
APP="dist/$NAME.app"

# 清理旧产物
rm -rf build dist

echo "▶ 用 PyInstaller 打包 $NAME (内置 tools/) …"
pyinstaller --noconfirm --clean \
  --windowed \
  --name "$NAME" \
  --add-data "tools:tools" \
  main.py

echo ""
echo "▶ 打包完成:"
ls -ld "$APP"
echo ""
echo "  运行: open '$APP'"
