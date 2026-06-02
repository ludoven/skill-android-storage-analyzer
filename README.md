# skill-android-storage-analyzer

一个面向 Codex 的 Android 存储分析 skill。  
通过 `adb` 对 Android 手机、平板、TV 盒子做只读存储扫描，输出 `🟢 / 🟡 / 🔴` 分级清理建议，并支持本地交互式 HTML 报告。

English README: [README.en.md](README.en.md)

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

## 适用场景

当用户出现这些需求时适合使用：

- “帮我看看 Android 设备存储空间”
- “电视盒子空间不够”
- “哪些目录最占空间”
- “Android 版存储分析”
- “帮我看看 `Android/media` / `Android/obb`”
- “能不能做一个像桌面版 storage-analyzer 的 Android 版本”

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

## 安装到 Codex

如果你要把 skill 放回 Codex 的 skill 目录，可直接复制：

```bash
cp -R android-storage-analyzer "${CODEX_HOME:-$HOME/.codex}/skills/"
```

然后重启 Codex。

## 依赖

- Python 3
- `adb`
- 一台已连接并可访问的 Android 设备

## 备注

这个仓库主要发布的是 skill 本体和示例报告，不是一个独立 GUI 应用。  
它的目标是让 Codex 在处理 Android 存储分析请求时，有稳定的脚本、参考文档和交互报告模板可复用。
