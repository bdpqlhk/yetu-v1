# 野兔 · 手机调试工具箱

一个面向测试/产品的桌面小工具,用于在日常开发中快速查看安卓 / 鸿蒙设备信息、已装应用、网络状态,设置全局代理,以及安装 APK / HAP 测试包。工具自带 `adb` / `hdc`,不依赖用户机器预装环境。

- 版本: 0.1.0
- 界面: Tkinter(ttk),macOS / Windows 均可打包
- 当前实现仅以 macOS 为打包目标(`build.sh`)

---

## 一、技术实现

### 1.1 总体架构

分五层,从上到下调用,方向单向:

```
main.py                    入口(--selftest 自检 / launch)
  └─ yetu/app.py           主窗口 YetuApp(Tk): 设备下拉 + Tab + 状态栏
       ├─ yetu/registry.py 面板注册表: @register_panel 装饰器收集
       ├─ yetu/ui/*.py     5 个功能面板(BasePanel 子类)
       ├─ yetu/core/device.py  设备抽象层(Device: serial + transport)
       ├─ yetu/core/adb.py     连接器层(Adb / Hdc 统一接口)
       └─ yetu/core/env.py     工具环境解析(内置 tools 优先)
```

```text
yetu/
├── app.py              主窗口: 设备选择、Notebook 面板、状态栏、异步调度
├── registry.py         面板注册表(@register_panel 装饰器)
├── core/
│   ├── env.py          定位内置 adb/hdc(打包态 / 开发态 / 系统 PATH 回退)
│   ├── adb.py          命令行封装: Adb / Hdc 两个连接器,命令差异在此收敛
│   └── device.py       设备抽象: 信息 / 应用 / 网络 / 代理 / 安装
└── ui/
    ├── base.py         面板基类 + 线程安全的后台执行(run_async)
    ├── device_panel.py   手机信息
    ├── apps_panel.py     已装应用
    ├── network_panel.py  网络信息
    ├── proxy_panel.py    全局代理
    └── install_panel.py  安装应用(APK / HAP)
```

### 1.2 核心设计

#### (1) 面板注册机制
- 每个面板用装饰器注册:`@register_panel(name="手机信息", order=10)`。
- `yetu/ui/__init__.py` 显式 `import` 各面板模块,触发装饰器执行。
- 主窗口 `app.py::_build_notebook` 遍历 `all_panels()`,按 `order` 排序后自动生成 Tab。
- **扩展新功能** = 新增一个 `BasePanel` 子类 + 注册 + 在 `ui/__init__.py` 加一行 import,主窗口无需改动。

#### (2) 连接器统一抽象(adb / hdc 差异收敛)
`yetu/core/adb.py` 中 `Adb` / `Hdc` 对外提供**同一套方法**,上层 `device.py` 与各面板不关心设备走哪种连接:

| 方法 | adb 实现 | hdc 实现 |
|---|---|---|
| `devices()` | `adb devices -l`(解析 model/status) | `hdc list targets`(过滤 `[Empty]`) |
| `shell()` | `adb -s <serial> shell` | `hdc -t <serial> shell` |
| `get_prop()` | `getprop key` | `param get key` |
| `list_packages()` | `pm list packages -3` | `bm list -p` |
| `package_version()` | `dumpsys package` | `bm dump -n` |
| `get/set/clear_proxy()` | `settings get/put global http_proxy` | 同,`settings` 命令 |
| `install()` | `adb install -r -t <apk>`(流式) | `hdc install <hap>`(流式) |
| `network_text()` | `ip addr` / `getprop` / `cmd wifi` | `ifconfig` |

`Hdc(Adb)` 继承 `Adb`,只覆写有差异的方法,尽量复用。

#### (3) 内置工具路径解析(`env.py::find_tool`)
工具查找优先级(返回第一个可执行文件):

1. 环境变量 `YETU_TOOLS/<子目录>/<name>`
2. 打包态(`sys.frozen`):exe 所在目录、`Contents/Resources`、`sys._MEIPASS`、`_internal` 下的 `tools/…` 或直接 `<子目录>/…`
3. 开发态:项目根 `tools/<子目录>/<name>`
4. 系统 `PATH`(`shutil.which`)兜底

> 打包后 macOS 上 tools 实际落在 `Contents/Frameworks/tools/`,PyInstaller 会自动建 `Contents/Resources/tools → ../Frameworks/tools` 软链去重,因此 `Contents/Resources` 候选也能命中。

#### (4) 线程模型
- Tkinter 非线程安全:所有耗时命令(adb/hdc)放后台线程执行。
- `BasePanel.run_async(fn, on_done, busy_widget, busy_text)`:`fn` 在子线程跑,完成后 `self.after(0, …)` 回主线程调 `on_done`。
- `busy_widget` 执行期间禁用按钮防重复点击,结束恢复按钮文字(`_set_busy` 会记住并还原原始文字)。

#### (5) 设备发现
`core/adb.py::list_all_devices` 同时跑 `adb devices -l` 与 `hdc list targets`,按 `(serial, transport)` 去重返回。同一台鸿蒙手机可能**同时**出现在 adb 与 hdc 中,界面分别标「安卓 / 鸿蒙」,方便用户选择对应条目装 APK 或 HAP。

#### (6) 自检模式
`python3 main.py --selftest` 不启动 GUI,打印:内置工具路径、已注册面板、当前设备。用于打包后快速冒烟验证。

### 1.3 打包

```bash
sh build.sh
# 产物: dist/野兔.app
```

`build.sh` 等价于:

```bash
pyinstaller --noconfirm --clean --windowed \
  --name 野兔 \
  --add-data "tools:tools" \
  main.py
```

要点:
- `--windowed`:无控制台窗口(适合双击打开)。
- `--add-data "tools:tools"`:把 `tools/adb`、`tools/hdc` 连同各自的库(`libusb_shared.dylib`)打进包。
- macOS onedir 产物为 `.app` bundle,adhoc 签名,本地直接可跑;分发到别的机器如遇 Gatekeeper 拦截,用 `xattr -dr com.apple.quarantine dist/野兔.app` 或右键打开。

---

## 二、使用说明

### 2.1 环境要求
- macOS 10.14+(打包产物自带 adb/hdc,无需预装)
- 手机开启 **开发者选项 + USB 调试**,用数据线连接电脑
- 首次连接安卓手机需在手机端确认「允许 USB 调试」授权弹窗

### 2.2 运行方式

| 场景 | 命令 |
|---|---|
| 开发运行(源码) | `python3 main.py` |
| 自检(不弹界面) | `python3 main.py --selftest` |
| 打包后运行 | `open dist/野兔.app`(或双击) |
| 重新打包 | `sh build.sh` |

### 2.3 界面操作

顶部工具栏:设备下拉框 + `刷新设备`;右侧显示内置工具状态(`adb: ✓` / `hdc: ✓`)。下方 5 个 Tab:

#### ① 手机信息
点 `刷新信息`,展示型号 / 厂商 / 系统版本 / API 级别 / 序列号 / ABI / 分辨率 / 屏幕密度 / 电池电量。单项读取失败显示 `—`。

#### ② 已装应用
- 默认只列第三方应用;取消勾选「仅第三方应用」可看全部。
- 支持按包名关键字搜索;右侧显示数量。
- 版本号对前 60 个包查询(避免逐包 dumpsys 过慢),其余显示 `—`。

#### ③ 网络信息
`刷新网络信息` 后展示:接口地址(`ip addr`)、DNS / 代理属性、WiFi 状态、当前全局代理。

#### ④ 全局代理
- `读取当前代理`:查看设备当前全局代理。
- 设置:填主机 + 端口,点 `设置代理`(用于 Charles / mitmproxy 抓包)。
- `清除代理`:恢复为未设置。

#### ⑤ 安装应用
1. 顶部选好目标设备(装 `.hap` 选「鸿蒙」条目,装 `.apk` 选「安卓」条目)。
2. `选择文件…` 选 `.apk` 或 `.hap`。
3. 点 `开始安装`,下方文本框流式显示安装进度,结束给出成功 / 失败结论。

### 2.4 常见问题
- **设备识别不到**:确认数据线支持数据传输、手机 USB 调试已开且已授权(必要时重启 adb server)。
- **按钮一直显示「加载中…」**:旧版本 bug,已修复;重新打包 `sh build.sh` 后运行。
- **首次装 .hap 报错**:请确认下拉框选的是该设备的「鸿蒙」条目(hdc serial 与 adb serial 不同)。

---

## 三、扩展开发
1. 新增面板:在 `yetu/ui/` 新建 `xxx_panel.py`,继承 `BasePanel`,`@register_panel(name=…, order=…)`,并在 `yetu/ui/__init__.py` import。
2. 新增设备能力:在 `core/device.py` 加方法(内部复用 `connector()`),或直接在某面板里调用 `Adb()/Hdc()`。
3. 更新内置工具:替换 `tools/adb/adb`、`tools/hdc/hdc`,重新 `sh build.sh`。
