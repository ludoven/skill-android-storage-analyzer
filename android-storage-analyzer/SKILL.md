---
name: android-storage-analyzer
description: Android device storage analysis over adb. Use when the user asks to inspect Android phone or tablet storage, says the device storage is full or nearly full, wants to know which folders or apps consume space, needs cleanup guidance for shared storage, `Android/media`, `Android/obb`, screenshots, downloads, vendor logs, or asks for an Android version of desktop storage analysis. Produces a read-only scan, cleanup triage, and optionally an HTML report.
---

# Android Storage Analyzer

## Overview

Analyze an Android device's storage over `adb` with a read-only workflow. Scan filesystem usage, identify large shared-storage directories and package-related media/obb footprints, classify cleanup actions into `🟢/🟡/🔴`, and optionally generate a local HTML report.

## Rules

- Keep the scan read-only. Allow `adb shell df`, `du`, `ls`, `find`, `getprop`, `dumpsys`, `pm list packages`.
- Do not run `adb shell rm`, `pm clear`, uninstall commands, or app-setting resets unless the user explicitly asks for cleanup execution and you confirm the exact target.
- Android 11+ often blocks direct reads of `/sdcard/Android/data`. Treat missing access as expected, report it, and continue with `Android/media`, `Android/obb`, shared storage, and package-level clues.
- Prefer `adb -s <serial>` when multiple devices are attached. If the user cares about a specific device, confirm or infer the serial first.

## Workflow

### Step 1. Scan The Device

Run the bundled scanner:

```bash
python3 scripts/scan.py --serial <adb-serial> > /tmp/android_storage_scan.json
```

If only one device is attached, `--serial` may be omitted:

```bash
python3 scripts/scan.py > /tmp/android_storage_scan.json
```

The scanner collects:
- Device identity and Android version
- `df` for `/data`, `/sdcard`, and `/storage/emulated`
- Top-level shared-storage directory sizes
- Large subdirectories under `Download`
- Large package-like directories under `Android/media` and `Android/obb`
- Warnings for denied paths or unsupported shell behavior

### Step 2. Analyze And Triage

Read [references/android.md](references/android.md), then inspect `/tmp/android_storage_scan.json`.

Do these tasks:
1. Pick the `Top 5` biggest actionable items.
2. Decide whether each item is:
   - `🟢 可优先清理`: shared-cache-like exports, bugreport/log directories, obviously disposable install payloads, or package assets that can be redownloaded and the user explicitly accepts the tradeoff.
   - `🟡 需人工判断`: photos, videos, downloads, chat media, `Android/media/<pkg>`, `Android/obb/<pkg>`, exported documents, voice notes.
   - `🔴 谨慎处理`: app uninstall/reset actions, shared storage tied to a still-used app, anything under system/private app data, or targets requiring `pm clear` / uninstall.
3. For unknown package directories, use the folder basename as a package clue and, if needed, run additional read-only commands such as:

```bash
adb -s <serial> shell pm list packages | grep '<pkg-fragment>'
adb -s <serial> shell ls -la '/sdcard/Android/media/<pkg>'
adb -s <serial> shell du -sk '/sdcard/Android/media/<pkg>'/*
```

4. Be explicit about Android limitations:
   - `/sdcard/Android/data` may be inaccessible
   - App-private `/data/data` and most of `/data/user*` are not safe scan targets without root
   - `obb` and `media` directories are not always pure cache

### Step 3. Build A Report

Write an analysis JSON with this schema:

```json
{
  "generated_at": "2026-06-02 12:00:00",
  "scan_seconds": 18.2,
  "system": {},
  "top5": [],
  "green": [],
  "yellow": [],
  "red": [],
  "denied": [],
  "summary": {
    "overview": "",
    "tier_stats": {
      "green": "约 12.4 GB",
      "yellow": "约 18.0 GB",
      "red": "约 6.3 GB"
    },
    "priority": [],
    "long_term": []
  }
}
```

For `green` items, prefer this richer shape so the interactive server can expose one-click execution:

```json
{
  "name": "旧安装包目录",
  "path": "/sdcard/Download/old-apks",
  "size_estimate": "约 2.4 GB",
  "commands": [
    {
      "label": "建议命令",
      "cmd": "adb -s <serial> shell rm -rf '/sdcard/Download/old-apks'"
    }
  ],
  "cleanup_actions": [
    {
      "label": "一键删除旧安装包",
      "command": "rm -rf '/sdcard/Download/old-apks'",
      "description": "会在当前 adb 设备上直接删除这个已确认的临时目录。"
    }
  ]
}
```

默认用交互服务模式：

```bash
python3 scripts/server.py /tmp/android_storage_analysis.json
```

服务模式会：
- 只对白名单里的 `green.cleanup_actions` 提供一键执行
- 用本地 `127.0.0.1` + 随机 token 暴露页面
- 执行时自动附带分析结果里的设备 serial
- 不给 `yellow` / `red` 项任何后台删除能力

仅当用户明确要一份可分享或留存的只读文件时，才生成静态报告：

```bash
python3 scripts/build_report.py /tmp/android_storage_analysis.json ~/Desktop/android-storage-report.html
```

静态报告只能查看和复制命令，不带一键执行。

### Step 4. Reply In Chat

Give a short conclusion-first summary:
- Device total / used / free storage
- Estimated space from `🟢` items
- The first 2-3 directories or app-related buckets the user should inspect
- The riskiest target that should not be deleted blindly

## Output Conventions

- Reuse the same visual structure as desktop storage analysis when possible: overview, `Top 5`, action items, `🟢/🟡/🔴`, long-term suggestions.
- In interactive mode, keep execution power narrow: only `green.cleanup_actions[].command` is executable.
- Keep path strings and package names literal.
- For suggested cleanup commands, prefer examples like:

```bash
adb -s <serial> shell rm -rf '/sdcard/Download/<known-temp-dir>'
adb -s <serial> shell pm clear <package>
adb -s <serial> uninstall <package>
```

Only show them as suggestions. Do not run them unless the user explicitly asks.

## Resources

### scripts/

- `scripts/scan.py`: Read-only adb scanner for Android storage
- `scripts/build_report.py`: Inject analysis JSON into the HTML report template
- `scripts/server.py`: Serve the report with allowlisted one-click adb execution for green items

### references/

- `references/android.md`: Android storage layout, triage rules, and safety notes

### assets/

- `assets/report_template.html`: Static HTML report template
