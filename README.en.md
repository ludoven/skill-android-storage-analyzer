# skill-android-storage-analyzer

An Android storage analysis skill for Codex.  
It scans Android phones, tablets, and TV boxes over `adb`, produces `🟢 / 🟡 / 🔴` cleanup guidance, and can render a local interactive HTML report.

中文说明: [README.md](README.md)

## 30-Second Quick Start

### 1. One-Line Install

If your environment already has Codex and the built-in `skill-installer`, run:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --url https://github.com/ludoven/skill-android-storage-analyzer/tree/main/android-storage-analyzer --method git
```

Then restart Codex.

### 2. How To Trigger It In Codex

You can say things like:

- `Check storage on the currently connected Android device`
- `Analyze why this Android TV box is running out of space`
- `Inspect which folders under /sdcard, Android/media, and Android/obb use the most storage`
- `Generate an Android storage cleanup report`
- `Use android-storage-analyzer on the connected device`

### 3. Shortest Example Prompt

```text
Use android-storage-analyzer to inspect the currently connected Android device storage
```

Or:

```text
Analyze this Android TV box storage and generate a cleanup report
```

## Who This Repo Is For

- Codex users
- People analyzing Android phone / tablet / TV box storage
- Anyone who does not want to manually assemble `adb shell du` and `df` commands
- Anyone who wants an HTML report instead of raw terminal output

## Features

- Read-only Android storage scanning over `adb`
- Coverage for `/data`, `/sdcard`, `Android/media`, `Android/obb`, `Download`, and related shared-storage paths
- Top 5 storage hotspots and triaged cleanup recommendations
- Static HTML report generation
- Local interactive report service
- Narrow execution model: only allowlisted `green.cleanup_actions` can be executed in interactive mode

## Repository Layout

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

## Typical Use Cases / Trigger Phrases

Use this skill when users ask things like:

- "Check Android device storage"
- "My TV box is running out of space"
- "Which folders are using the most storage?"
- "Inspect `Android/media` or `Android/obb`"
- "Build an Android version of desktop storage-analyzer"

You can also explicitly write:

- `Use $android-storage-analyzer to inspect current Android device storage`

## What Codex Will Actually Do

After the skill is triggered, Codex is guided to:

1. run a read-only `adb` scan
2. identify large directories and app-related storage areas
3. classify findings into `🟢 / 🟡 / 🔴`
4. generate a static or interactive HTML report
5. provide cleanup guidance in plain language

## Workflow

### 1. Scan

```bash
python3 android-storage-analyzer/scripts/scan.py --serial <adb-serial> > /tmp/android_storage_scan.json
```

If only one device is attached:

```bash
python3 android-storage-analyzer/scripts/scan.py > /tmp/android_storage_scan.json
```

### 2. Produce Analysis JSON

Interpret the scan output using the rules in `SKILL.md` and `references/android.md`.

### 3. Generate Static Report

```bash
python3 android-storage-analyzer/scripts/build_report.py /tmp/android_storage_analysis.json ~/Desktop/android-storage-report.html
```

### 4. Run Interactive Report

```bash
python3 android-storage-analyzer/scripts/server.py /tmp/android_storage_analysis.json
```

Interactive mode:

- binds to `127.0.0.1`
- injects a random token
- only executes `green.cleanup_actions`
- never executes `yellow` or `red` actions

## Safety Model

- The default scan is read-only
- Destructive commands such as `rm`, `pm clear`, or uninstall are not run automatically
- `/sdcard/Android/data` visibility may be restricted on Android 11+, which is expected platform behavior
- No root-only private app data scanning is attempted
- Interactive execution is restricted to allowlisted actions declared in the analysis JSON

## Included Test Report

This repository includes one real-device test artifact set:

- Device: `E300`
- Android: `11.1`
- Report: [reports/e300-android-storage-report.html](reports/e300-android-storage-report.html)
- Analysis JSON: [reports/e300-android-storage-analysis.json](reports/e300-android-storage-analysis.json)

Test result summary:

- The device storage state is healthy
- `/data` and `/sdcard` are both around `60%` used
- Storage usage mostly comes from installed apps rather than media, downloads, or shared-storage clutter
- No `green` one-click cleanup target was identified on this device

## Manual Install Into Codex

To place the skill back into a Codex skills directory:

```bash
cp -R android-storage-analyzer "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Then restart Codex.

## GitHub Pages

If GitHub Pages is enabled for this repository, the default entry page redirects to the included test report:

- Pages home:
  `https://ludoven.github.io/skill-android-storage-analyzer/`
- Direct report URL:
  `https://ludoven.github.io/skill-android-storage-analyzer/reports/e300-android-storage-report.html`

## Requirements

- Python 3
- `adb`
- A connected Android device

## Notes

This repository publishes the skill itself plus sample reports.  
It is not a standalone GUI application; it is a reusable Codex skill package.
