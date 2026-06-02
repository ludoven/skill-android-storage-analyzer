# skill-android-storage-analyzer

一个面向 Codex 的 Android 存储分析 skill。  
通过 `adb` 对 Android 手机、平板、TV 盒子做只读存储扫描，输出 `🟢 / 🟡 / 🔴` 分级清理建议，并支持本地交互式 HTML 报告。

English README: [README.en.md](README.en.md)

## 先看效果

- 在线报告页：
  [https://ludoven.github.io/skill-android-storage-analyzer/reports/e300-android-storage-report.html](https://ludoven.github.io/skill-android-storage-analyzer/reports/e300-android-storage-report.html)
- GitHub Pages 首页：
  [https://ludoven.github.io/skill-android-storage-analyzer/](https://ludoven.github.io/skill-android-storage-analyzer/)

## 30 秒上手

### 1. 一句话安装

如果你的环境里已经有 Codex 和内置 `skill-installer`，直接运行：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --url https://github.com/ludoven/skill-android-storage-analyzer/tree/main/android-storage-analyzer --method git
```

安装后重启 Codex。

### 2. 在 Codex 里怎么触发

你可以直接对 Codex 说这些话：

- `帮我看看这台 Android 设备存储空间`
- `分析一下这个电视盒子为什么空间不够`
- `看看 /sdcard、Android/media、Android/obb 哪些最占空间`
- `给我一份 Android 存储清理报告`
- `用 android-storage-analyzer 看一下当前连接设备`

### 3. 最短使用示例

如果你已经把设备连上 `adb`，直接对 Codex 说：

```text
用 android-storage-analyzer 看一下当前连接的 Android 设备存储
```

或者更明确一点：

```text
帮我分析一下这台电视盒子的存储占用，并生成一份清理报告
```

## 这个仓库适合谁

- 正在用 Codex
- 想分析 Android 手机 / 平板 / TV 盒子空间占用
- 不想手动拼 `adb shell du` / `df` 命令
- 想要一份 HTML 报告，而不是零散终端输出

## 功能

- 通过 `adb` 扫描 Android 设备存储
- 统计 `/data`、`/sdcard`、`Android/media`、`Android/obb`、`Download` 等目录
- 识别共享存储中的大目录和应用相关目录
- 输出 `Top 5` 占用项和 `🟢 / 🟡 / 🔴` 清理建议
- 生成静态 HTML 报告
- 通过本地 `server.py` 提供交互式报告
- 交互模式下，仅对白名单 `green.cleanup_actions` 开放一键执行

## 目录结构

```text
skill-android-storage-analyzer/
├── android-storage-analyzer/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── assets/report_template.html
│   ├── references/android.md
│   └── scripts/
│       ├── scan.py
│       ├── build_report.py
│       └── server.py
├── reports/
│   ├── e300-android-storage-analysis.json
│   └── e300-android-storage-report.html
├── README.md
└── README.en.md
```

## 适用场景 / 触发词

当用户出现这些需求时适合使用：

- “帮我看看 Android 设备存储空间”
- “电视盒子空间不够”
- “哪些目录最占空间”
- “Android 版存储分析”
- “帮我看看 `Android/media` / `Android/obb`”
- “能不能做一个像桌面版 storage-analyzer 的 Android 版本”

也可以显式写：

- `Use $android-storage-analyzer to inspect current Android device storage`
- `用 $android-storage-analyzer 分析当前设备空间`

## Codex 实际会做什么

触发后，这个 skill 会引导 Codex：

1. 通过 `adb` 做只读扫描
2. 找出占空间最大的目录或应用相关区域
3. 分成 `🟢 / 🟡 / 🔴` 三类
4. 生成静态或交互式 HTML 报告
5. 给出适合小白理解的清理建议

## 工作方式

### 1. 扫描

```bash
python3 android-storage-analyzer/scripts/scan.py --serial <adb-serial> > /tmp/android_storage_scan.json
```

如果只有一台设备：

```bash
python3 android-storage-analyzer/scripts/scan.py > /tmp/android_storage_scan.json
```

### 2. 生成分析 JSON

根据 `SKILL.md` 和 `references/android.md` 中的规则，把扫描结果整理成分析 JSON。

### 3. 静态报告

```bash
python3 android-storage-analyzer/scripts/build_report.py /tmp/android_storage_analysis.json ~/Desktop/android-storage-report.html
```

### 4. 交互式报告

```bash
python3 android-storage-analyzer/scripts/server.py /tmp/android_storage_analysis.json
```

交互式模式特点：

- 本地服务绑定 `127.0.0.1`
- 使用随机 token 防止误调用
- 只允许执行 `green.cleanup_actions`
- `yellow` 和 `red` 只展示，不可后台删除

## 安全边界

- 默认扫描流程只读
- 不自动运行 `rm`、`pm clear`、卸载等破坏性命令
- Android 11+ 上 `/sdcard/Android/data` 可见性可能受限，这是系统限制
- 无 root 时不尝试扫描 `/data/data`、`/data/user/0` 等私有目录
- 交互执行严格依赖分析 JSON 中白名单动作，不允许任意命令注入

## 这次附带的测试报告

仓库包含一次真实设备测试产物：

- 设备：`E300`
- Android：`11.1`
- 报告文件： [reports/e300-android-storage-report.html](reports/e300-android-storage-report.html)
- 分析文件： [reports/e300-android-storage-analysis.json](reports/e300-android-storage-analysis.json)

本次测试结论：

- 盒子存储总体健康，没有明显共享存储垃圾
- `/data` 和 `/sdcard` 约使用 `60%`
- 主要占用来自应用本体，而不是媒体、下载或缓存目录
- 没有发现值得作为 `green` 一键清理对象的目录

## 手动安装到 Codex

如果你要把 skill 放回 Codex 的 skill 目录，可直接复制：

```bash
cp -R android-storage-analyzer "${CODEX_HOME:-$HOME/.codex}/skills/"
```

然后重启 Codex。

## GitHub Pages

如果仓库启用了 GitHub Pages，默认入口会直接跳转到这次附带的测试报告：

- Pages 首页：
  `https://ludoven.github.io/skill-android-storage-analyzer/`
- 报告直链：
  `https://ludoven.github.io/skill-android-storage-analyzer/reports/e300-android-storage-report.html`

## 依赖

- Python 3
- `adb`
- 一台已连接并可访问的 Android 设备

## 备注

这个仓库主要发布的是 skill 本体和示例报告，不是一个独立 GUI 应用。  
它的目标是让 Codex 在处理 Android 存储分析请求时，有稳定的脚本、参考文档和交互报告模板可复用。
